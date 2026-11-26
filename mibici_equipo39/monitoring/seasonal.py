"""Contrasta entradas, objetivo y predicción con una referencia de la misma temporada."""

import argparse
import json
import os
from pathlib import Path
from importlib.metadata import version

import numpy as np
import pandas as pd

from .common import ROOT, load_config, model_input, save_json, sha256, validate_frame, verified_dataset
from .drift import export_variables

KEYS = ["station_id", "prediction_time"]
TARGET = "target_departures"
PREDICTION = "prediction_a"
DEFAULT_REPORT = ROOT / "reports/etapa5/correccion_20261125"


def attach_predictions(frame, predictions):
    """Une por clave; nunca acepta correspondencia basada solamente en orden de filas."""
    required = KEYS + [TARGET, PREDICTION]
    if not set(required).issubset(predictions) or predictions[KEYS].isna().any().any():
        raise ValueError("Faltan claves o columnas de predicción.")
    if frame.duplicated(KEYS).any() or predictions.duplicated(KEYS).any() or len(frame) != len(predictions):
        raise ValueError("Las claves de predicción deben ser únicas y completas.")
    result = frame.merge(predictions[required], on=KEYS, how="left", validate="one_to_one", suffixes=("", "_check"))
    if not result[TARGET].equals(result[TARGET + "_check"]):
        raise ValueError("Las etiquetas o claves de las predicciones no coinciden.")
    values = result[PREDICTION].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("La predicción debe ser finita y no negativa.")
    return result.drop(columns=TARGET + "_check")


def seasonal_pair(reference, current, config):
    """Mismo mes del año anterior y mismas estaciones, con mallas completas."""
    start = pd.Timestamp(config["current_start"]) - pd.DateOffset(years=1)
    end = pd.Timestamp(config["current_end"]) - pd.DateOffset(years=1)
    seasonal = reference.loc[reference.prediction_time.ge(start) & reference.prediction_time.lt(end)].copy()
    if seasonal.empty:
        raise ValueError("No hay referencia de la misma temporada; no sustituirla por otro mes.")
    cohort = sorted(set(seasonal.station_id) & set(current.station_id))
    if not cohort:
        raise ValueError("No hay estaciones comunes entre temporadas.")
    seasonal = seasonal.loc[seasonal.station_id.isin(cohort)].copy()
    current = current.loc[current.station_id.isin(cohort)].copy()
    validate_frame(seasonal, start, end, config)
    validate_frame(current, config["current_start"], config["current_end"], config)
    return seasonal, current, {"reference_start": str(start.date()), "reference_end_exclusive": str(end.date()),
                               "current_start": config["current_start"], "current_end_exclusive": config["current_end"],
                               "stations": len(cohort), "reference_rows": len(seasonal), "current_rows": len(current)}


def describe(frame):
    y, p = frame[TARGET].to_numpy(dtype=float), frame[PREDICTION].to_numpy(dtype=float)
    error = p-y
    return {"rows": len(frame), "observed_mean": float(y.mean()), "predicted_mean": float(p.mean()),
            "departures": int(y.sum()), "bias_prediction_minus_observed": float(error.mean()),
            "aggregate_underestimate_pct": float(100*(y.sum()-p.sum())/y.sum()) if y.sum() else None,
            "mae": float(np.abs(error).mean()), "rmse": float(np.sqrt((error**2).mean()))}


def standardized_comparison(reference, current):
    """Pondera igual estación, día de semana y hora para aislar mezcla de calendario."""
    groups = ["station_id", "day_of_week", "hour_of_day"]
    a = reference.groupby(groups, observed=True)[[TARGET, PREDICTION]].mean().sort_index()
    b = current.groupby(groups, observed=True)[[TARGET, PREDICTION]].mean().sort_index()
    if not a.index.equals(b.index):
        raise ValueError("No coinciden los estratos de calendario y estación.")
    result = {"method": "equal_station_weekday_hour_weights", "strata": len(a)}
    for col in (TARGET, PREDICTION):
        old, new = float(a[col].mean()), float(b[col].mean())
        result[col] = {"reference_mean": old, "current_mean": new,
                       "change_pct": 100*(new/old-1) if old else None}
    return result


def make_report(reference, current, config, label, output):
    os.environ.setdefault("DO_NOT_TRACK", "1")
    from evidently import DataDefinition, Dataset, Report
    from evidently.metrics import ValueDrift
    from evidently.presets import DataDriftPreset, DataSummaryPreset

    columns = config["features"] + [TARGET, PREDICTION]
    definition = DataDefinition(categorical_columns=config["categorical"],
                                numerical_columns=config["numerical"] + [TARGET, PREDICTION])
    datasets, sampling = [], {}
    for name, frame in (("reference", reference), ("current", current)):
        sample = frame.sample(n=min(len(frame), config["drift_sample_size"]), random_state=config["seed"]).sort_values(KEYS)
        data = model_input(sample, config)
        data[TARGET], data[PREDICTION] = sample[TARGET].astype(float), sample[PREDICTION]
        datasets.append(Dataset.from_pandas(data, data_definition=definition))
        sampling[name] = {"population_rows": len(frame), "sample_rows": len(sample), "seed": config["seed"]}
    # La alerta global sigue usando solo las nueve entradas; las salidas tienen alertas propias.
    feature_drift = DataDriftPreset(columns=config["features"], drift_share=config["drift_share"],
                                   cat_method=config["categorical_method"], num_method=config["numerical_method"],
                                   cat_threshold=config["drift_threshold"], num_threshold=config["drift_threshold"])
    snapshot = Report([ValueDrift(column=TARGET, method="wasserstein", threshold=.1),
                       ValueDrift(column=PREDICTION, method="wasserstein", threshold=.1),
                       feature_drift, DataSummaryPreset()],
                      metadata={"team":"39", "comparison":label, "model_version":"1",
                                "protocol_sha256":config["protocol_sha256"]}).run(
        reference_data=datasets[0], current_data=datasets[1], name=f"P1 demanda y predicción — {label}")
    snapshot.save_html(str(output / f"drift_{label}.html"))
    payload = json.loads(snapshot.json())
    save_json(output / f"drift_{label}.json", payload)
    variables = export_variables(payload, {**config, "features":columns})
    variables["role"] = variables.variable.map(lambda col: "target" if col==TARGET else "prediction" if col==PREDICTION else "feature")
    variables.to_csv(output / f"drift_{label}_variables.csv", index=False)
    return {"sampling":sampling, "features_drifted":int(variables.loc[variables.role.eq("feature"),"drift"].sum()),
            "features_total":len(config["features"]), "variables":variables.to_dict(orient="records")}


def generate(predictions_dir, report_dir):
    config = load_config()
    output, inputs = Path(report_dir), Path(predictions_dir)
    output.mkdir(parents=True, exist_ok=True)
    pred_manifest = json.loads((inputs / "manifest.json").read_text(encoding="utf-8"))
    model = json.loads((ROOT / "references/etapa4/model_manifest.json").read_text(encoding="utf-8"))
    if (pred_manifest["protocol_sha256"] != config["protocol_sha256"]
            or pred_manifest["bundle_sha256"] != model["bundle_sha256"]
            or pred_manifest["source_run_id"] != config["expected_a_run"]
            or pred_manifest["model_version"] != config["expected_a_version"]):
        raise ValueError("Linaje de predicciones distinto del modelo A aprobado.")
    frames, populations = {}, {}
    for name in ("reference", "current"):
        frame, manifest = verified_dataset(name, config)
        spec = pred_manifest["files"][name]
        path = inputs / f"{name}_predictions.parquet"
        if sha256(path) != spec["sha256"] or spec["data_sha256"] != manifest["files"][name]["sha256"]:
            raise ValueError("Las huellas de datos o predicciones cambiaron.")
        frame = attach_predictions(frame, pd.read_parquet(path))
        validate_frame(frame, config[f"{name}_start"], config[f"{name}_end"], config)
        frames[name] = frame
        populations[name] = describe(frame)
    seasonal, current, periods = seasonal_pair(frames["reference"], frames["current"], config)
    populations["october_2025"] = describe(seasonal)
    populations["october_2026"] = describe(current)
    comparisons = {"historico":make_report(frames["reference"], frames["current"],config,"historico",output),
                   "estacional":make_report(seasonal,current,config,"estacional",output)}
    summary = {"protocol_sha256":config["protocol_sha256"], "model":{k:pred_manifest[k] for k in ("model_name","model_version","source_run_id","bundle_sha256")},
               "prediction_files":pred_manifest["files"], "populations":populations, "seasonal_periods":periods,
               "historical_target_change_pct":100*(populations["current"]["observed_mean"]/populations["reference"]["observed_mean"]-1),
               "seasonal_target_change_pct":100*(populations["october_2026"]["observed_mean"]/populations["october_2025"]["observed_mean"]-1),
               "standardized":standardized_comparison(seasonal,current), "comparisons":comparisons,
               "reference_performance_in_sample":True, "no_new_training":True, "no_alias_changed":True,
               "limitations":["Octubre 2025 pertenece al entrenamiento de A: su error es descriptivo, no un test independiente.",
                              "Una comparación interanual no prueba causalidad ni concept drift.",
                              "Se conservan ceros por ausencia de viajes; no hay inventario de bicicletas ni cierres comprobados."],
               "environment":{name:version(name) for name in ("evidently","pandas","numpy","pyarrow")}}
    save_json(output / "resumen.json", summary)
    segments = []
    for label, frame in (("october_2025",seasonal),("october_2026",current)):
        for col in ("hour_of_day","is_weekend"):
            for key, part in frame.groupby(col,observed=True):
                segments.append({"period":label,"group":col,"segment":int(key),**describe(part)})
    pd.DataFrame(segments).to_csv(output / "error_segmentos.csv",index=False)
    daily = pd.concat([frame.assign(period=label) for label,frame in (("2025",seasonal),("2026",current))])
    daily["day"] = daily.prediction_time.dt.day
    daily.groupby(["period","day"],observed=True)[[TARGET,PREDICTION]].mean().reset_index().to_csv(output / "demanda_diaria.csv",index=False)
    print(json.dumps({"historical_change_pct":summary["historical_target_change_pct"],"seasonal_change_pct":summary["seasonal_target_change_pct"],"populations":populations},ensure_ascii=False))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--predictions-dir", default=str(ROOT / "private_results/etapa5/seasonal"))
    cli.add_argument("--report-dir", default=str(DEFAULT_REPORT))
    args = cli.parse_args()
    generate(args.predictions_dir, args.report_dir)
