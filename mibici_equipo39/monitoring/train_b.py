"""Actualiza la media estacional con doce meses y registra B sin modificar champion."""

import json
from time import perf_counter

import numpy as np

from mibici_equipo39.modeling.p1 import SeasonalMeanBaseline
from mibici_equipo39.modeling.tracking import git_state
from .common import ROOT, load_config, model_input, parser, save_json, validate_frame, verified_dataset
from .registry import freeze, tracking


def train(config):
    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature
    freeze(config)
    client = tracking(config)
    path = ROOT / "references/etapa5/models.json"
    models = json.loads(path.read_text(encoding="utf-8"))
    frame, manifest = verified_dataset("train_b", config)
    validate_frame(frame, config["training_b_start"], config["training_b_end"], config)
    if "b" in models:
        b = client.get_model_version(config["model_name"], models["b"]["version"])
        if b.run_id != models["b"]["run_id"] or models["b"]["training_sha256"] != manifest["files"]["train_b"]["sha256"]:
            raise ValueError("La versión B existente no corresponde a este entrenamiento.")
        if b.status != "READY" or client.get_run(b.run_id).info.status != "FINISHED":
            raise ValueError("La corrida B debe estar terminada y su versión lista antes de reutilizarla.")
        print(f"B ya registrada y verificada: versión {b.version}.")
        return
    X = model_input(frame, config).reset_index(drop=True)
    y = frame.target_departures.reset_index(drop=True)
    commit, dirty = git_state()
    if dirty:
        raise ValueError("Confirma primero el código y el protocolo en Git para registrar un entrenamiento trazable.")
    start = perf_counter()
    model = SeasonalMeanBaseline().fit(X, y)
    seconds = perf_counter()-start
    # La inferencia de firma usa filas históricas; octubre no interviene en fit ni selección.
    sample = X.head(5)
    prediction = np.asarray(model.predict(sample), dtype="float64")
    mlflow.set_experiment(config["experiment"])
    with mlflow.start_run(run_name="E5-p1-B-media-estacional-12meses-Marco") as run:
        mlflow.set_tags({"team": "39", "question": "p1", "stage_of_work": "monitoring_candidate",
                         "mlflow.source.name": "mibici_equipo39.monitoring.train_b",
                         "executor": "Marco", "git_commit": commit, "git_dirty": "false",
                         "protocol_sha256": config["protocol_sha256"], "model_family": "seasonal_mean",
                         "historical_data_version": config["historical_data_version"]})
        mlflow.log_params({"train_start": config["training_b_start"], "train_end_exclusive": config["training_b_end"],
                           "seed": config["seed"], "cohort_stations": int(X.station_id.nunique()), "rows": len(X),
                           "aggregation": "station_day_hour,station_hour,global", "training_sha256": manifest["files"]["train_b"]["sha256"]})
        mlflow.log_metric("training_seconds", seconds)
        requirements = [line for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines() if line and not line.startswith("#")]
        info = mlflow.sklearn.log_model(model, name="model", signature=infer_signature(sample, prediction),
                                       input_example=sample, serialization_format="cloudpickle", pip_requirements=requirements,
                                       code_paths=[str(ROOT / "mibici_equipo39")])
        mlflow.log_dict(config, "config/protocolo.json")
        mlflow.log_dict(manifest, "data/manifest.json")
        mlflow.set_tag("model_uri", info.model_uri)
        version = mlflow.register_model(info.model_uri, config["model_name"])
        client.update_model_version(config["model_name"], version.version,
                                    description="Etapa 5. Media por estación, día y hora reentrenada con octubre 2025 a septiembre 2026. Candidata B; octubre 2026 reservado para evaluación pareada. Sin promoción automática.")
        client.set_model_version_tag(config["model_name"], version.version, "protocol_sha256", config["protocol_sha256"])
        client.set_model_version_tag(config["model_name"], version.version, "git_commit", commit)
        models["b"] = {"version": version.version, "run_id": run.info.run_id,
                        "uri": f"models:/{config['model_name']}/{version.version}", "model_uri": info.model_uri,
                        "training_sha256": manifest["files"]["train_b"]["sha256"], "git_commit": commit,
                        "family": "seasonal_mean", "status": "candidate_not_promoted"}
        save_json(path, models)
        save_json(ROOT / config["report_dir"] / "entrenamiento_b.json",
                  {**models["b"], "training_seconds": seconds, "rows": len(X), "stations": int(X.station_id.nunique()),
                   "a_training_seconds": None, "a_training_cost_note": "No se recuperó un tiempo comparable de entrenamiento de A; no se estima ni inventa."})
    champion = client.get_model_version_by_alias(config["model_name"], config["model_alias"])
    if champion.version != models["a"]["version"]:
        raise RuntimeError("El alias cambió durante el trabajo; detener la integración y revisar.")
    print(json.dumps({"a": models["a"]["version"], "b": models["b"]["version"], "champion_unchanged": True}))


if __name__ == "__main__":
    args = parser(__doc__).parse_args()
    train(load_config(args.config))
