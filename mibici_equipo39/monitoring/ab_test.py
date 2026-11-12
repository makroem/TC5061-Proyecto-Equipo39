"""Evaluación retrospectiva pareada; no asigna tráfico ni modifica modelos en producción."""

import json
from pathlib import Path
from time import perf_counter

import numpy as np
import pandas as pd

from .common import ROOT, load_config, model_input, parser, save_json, validate_frame, verified_dataset
from .metrics import block_bootstrap, improvement, metrics
from .registry import tracking


def latency(models, X, config):
    batch = X.head(config["latency_batch_size"])
    for model in models.values():
        for _ in range(3): model.predict(batch)
    times = {name: [] for name in models}
    for iteration in range(config["latency_repeats"]):
        for name in (list(models) if iteration % 2 == 0 else list(models)[::-1]):
            start = perf_counter()
            models[name].predict(batch)
            times[name].append((perf_counter()-start)*1000)
    return {name: {"batch_rows": len(batch), "repeats": len(values), "median_ms": float(np.median(values)),
                   "p95_ms": float(np.quantile(values, .95))} for name, values in times.items()}


def evaluate(config):
    import mlflow
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    client = tracking(config)
    versions = json.loads((ROOT / "references/etapa5/models.json").read_text(encoding="utf-8"))
    if versions["protocol_sha256"] != config["protocol_sha256"] or "b" not in versions:
        raise ValueError("Falta fijar y registrar B con el protocolo vigente.")
    frame, manifest = verified_dataset("current", config)
    validate_frame(frame, config["current_start"], config["current_end"], config)
    X = model_input(frame, config)
    y = frame.target_departures.to_numpy()
    models = {name: mlflow.pyfunc.load_model(versions[name]["uri"]) for name in ("a", "b")}
    signatures = {name: model.metadata.signature.to_dict() for name, model in models.items()}
    if signatures["a"] != signatures["b"]:
        raise ValueError("Las firmas de A y B no coinciden.")
    predictions = {name: np.asarray(model.predict(X), dtype=float).reshape(-1) for name, model in models.items()}
    result = {name: metrics(y, prediction) for name, prediction in predictions.items()}
    if any((prediction < 0).any() for prediction in predictions.values()):
        raise ValueError("El modelo de conteos devolvió predicciones negativas.")
    result["mae_improvement_pct"] = improvement(result["a"]["mae"], result["b"]["mae"])
    result["rmse_improvement_pct"] = improvement(result["a"]["rmse"], result["b"]["rmse"])
    result["bootstrap"] = block_bootstrap(frame.prediction_time, y, predictions["a"], predictions["b"],
                                          config["bootstrap_block_days"], config["bootstrap_repeats"], config["seed"])
    result["latency"] = latency(models, X, config)
    sizes = {}
    for name in ("a", "b"):
        target = ROOT / config["private_dir"] / "models" / name
        target.mkdir(parents=True, exist_ok=True)
        downloaded = Path(mlflow.artifacts.download_artifacts(artifact_uri=versions[name]["uri"], dst_path=str(target)))
        sizes[name] = {"bundle_bytes": sum(p.stat().st_size for p in downloaded.rglob("*") if p.is_file()),
                       "serialized_model_bytes": sum(p.stat().st_size for p in downloaded.rglob("*.pkl"))}
    result["model_size"] = sizes
    result["evaluation"] = {"design": "offline_paired_retrospective", "current_sha256": manifest["files"]["current"]["sha256"],
                            "rows_both_models": len(X), "same_keys_and_targets": True, "protocol_sha256": config["protocol_sha256"],
                            "a_version": versions["a"]["version"], "b_version": versions["b"]["version"]}
    comparisons = []
    def add_segment(kind, name, mask):
        scores = {key: metrics(y[mask], values[mask]) for key, values in predictions.items()}
        comparisons.append({"group": kind, "segment": str(name), "rows": int(mask.sum()),
                            "a_mae": scores["a"]["mae"], "b_mae": scores["b"]["mae"],
                            "a_rmse": scores["a"]["rmse"], "b_rmse": scores["b"]["rmse"],
                            "mae_improvement_pct": improvement(scores["a"]["mae"], scores["b"]["mae"])})
    add_segment("overall", "all", np.ones(len(y), dtype=bool))
    for column in ("is_weekend", "hour_of_day", "station_id"):
        for value in sorted(frame[column].unique()):
            add_segment(column, value, frame[column].eq(value).to_numpy())
    weeks = ((frame.prediction_time.dt.day - 1) // 7) + 1
    for week in sorted(weeks.unique()): add_segment("week_of_month", week, weeks.eq(week).to_numpy())
    scores = pd.DataFrame(comparisons)
    priority = scores[scores.group.isin(["is_weekend", "hour_of_day"])].mae_improvement_pct
    conditions = {"mae_improves_5pct": result["mae_improvement_pct"] is not None and result["mae_improvement_pct"] >= config["promotion_min_mae_improvement_pct"],
                  "rmse_within_tolerance": result["rmse_improvement_pct"] is not None and result["rmse_improvement_pct"] >= -config["promotion_max_rmse_increase_pct"],
                  "priority_segments_within_tolerance": bool(priority.notna().all() and priority.ge(-config["promotion_max_segment_mae_increase_pct"]).all()),
                  "ci_supports_lower_mae": result["bootstrap"]["ci95_high"] < 0,
                  "latency_within_tolerance": result["latency"]["b"]["p95_ms"] <= config["promotion_max_latency_ratio"] * result["latency"]["a"]["p95_ms"]}
    result["promotion_checks"] = conditions
    result["recommendation"] = "review_b_before_promotion" if all(conditions.values()) else "retain_a_and_investigate"
    report = ROOT / config["report_dir"]
    report.mkdir(parents=True, exist_ok=True)
    scores.to_csv(report / "ab_metricas.csv", index=False)
    save_json(report / "ab_resultados.json", result)
    save_json(report / "compatibilidad_modelos.json", {"a_version": versions["a"]["version"], "b_version": versions["b"]["version"],
                                                       "signature_equal": True, "signature": signatures["a"],
                                                       "input_rows": len(X), "finite_predictions": True,
                                                       "nonnegative_predictions": True})
    private = ROOT / config["private_dir"]
    private.mkdir(parents=True, exist_ok=True)
    frame[["station_id", "prediction_time", "target_departures"]].assign(a=predictions["a"], b=predictions["b"]).to_parquet(private / "predicciones.parquet", index=False)
    daily = pd.DataFrame({"date": frame.prediction_time.dt.normalize(),
                          "A": np.abs(predictions["a"]-y), "B": np.abs(predictions["b"]-y)}).groupby("date").mean()
    ax = daily.plot(figsize=(10, 4), ylabel="MAE: viajes por estación-hora", xlabel="Octubre de 2026", title="Error diario en las mismas observaciones")
    ax.figure.tight_layout()
    ax.figure.savefig(report / "error_diario.png", dpi=160)
    plt.close(ax.figure)
    mlflow.set_experiment(config["experiment"])
    with mlflow.start_run(run_name="E5-p1-comparacion-pareada-octubre-Marco") as run:
        mlflow.set_tags({"team": "39", "question": "p1", "stage_of_work": "monitoring_evaluation", "executor": "Marco",
                         "mlflow.source.name": "mibici_equipo39.monitoring.ab_test",
                         "protocol_sha256": config["protocol_sha256"], "a_run_id": versions["a"]["run_id"], "b_run_id": versions["b"]["run_id"]})
        for name in ("a", "b"):
            mlflow.log_metrics({f"current_{name}_{metric}": value for metric, value in result[name].items()})
        for file in ("ab_metricas.csv", "ab_resultados.json", "error_diario.png"):
            mlflow.log_artifact(str(report / file), "evaluation")
        mlflow.log_dict(manifest, "data/manifest.json")
        mlflow.log_dict(config, "config/protocolo.json")
        result["evaluation_run_id"] = run.info.run_id
    champion = client.get_model_version_by_alias(config["model_name"], config["model_alias"])
    result["champion_unchanged"] = champion.version == versions["a"]["version"]
    save_json(report / "ab_resultados.json", result)
    print(json.dumps({key: result[key] for key in ("a", "b", "mae_improvement_pct", "recommendation", "champion_unchanged")}))


if __name__ == "__main__":
    args = parser(__doc__).parse_args()
    evaluate(load_config(args.config))
