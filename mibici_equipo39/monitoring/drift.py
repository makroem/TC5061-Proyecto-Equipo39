"""Genera el reporte Evidently con la muestra reproducible del protocolo."""

import json
import os
from importlib.metadata import version

import pandas as pd

from .common import ROOT, load_config, model_input, parser, save_json, validate_frame, verified_dataset


def export_variables(payload, config):
    rows = []
    for metric in payload["metrics"]:
        settings = metric["config"]
        if settings["type"].endswith(":ValueDrift"):
            rows.append({"variable": settings["column"], "method": settings["method"],
                         "threshold": settings["threshold"], "score": float(metric["value"]),
                         "drift": float(metric["value"]) >= settings["threshold"]})
    if {row["variable"] for row in rows} != set(config["features"]) or len(rows) != len(config["features"]):
        raise ValueError("El reporte no contiene exactamente las variables esperadas.")
    return pd.DataFrame(rows)


def generate(config):
    os.environ.setdefault("DO_NOT_TRACK", "1")
    from evidently import DataDefinition, Dataset, Report
    from evidently.presets import DataDriftPreset, DataSummaryPreset
    reference, manifest = verified_dataset("reference", config)
    current, _ = verified_dataset("current", config)
    quality = {"reference": validate_frame(reference, config["reference_start"], config["reference_end"], config),
               "current": validate_frame(current, config["current_start"], config["current_end"], config)}
    definition = DataDefinition(categorical_columns=config["categorical"], numerical_columns=config["numerical"])
    datasets = []
    samples = {}
    for name, frame in (("reference", reference), ("current", current)):
        sample = frame.sample(n=min(len(frame), config["drift_sample_size"]), random_state=config["seed"]).sort_values(["station_id", "prediction_time"])
        X = model_input(sample, config)
        datasets.append(Dataset.from_pandas(X, data_definition=definition))
        samples[name] = {"rows": len(X), "population_rows": len(frame), "method": "uniform_without_replacement", "seed": config["seed"]}
    preset = DataDriftPreset(columns=config["features"], drift_share=config["drift_share"],
                            cat_method=config["categorical_method"], num_method=config["numerical_method"],
                            cat_threshold=config["drift_threshold"], num_threshold=config["drift_threshold"])
    snapshot = Report([preset, DataSummaryPreset()], metadata={"team": "39", "question": "p1", "protocol_sha256": config["protocol_sha256"]}).run(
        reference_data=datasets[0], current_data=datasets[1], name="Equipo 39: P1, referencia histórica frente a octubre 2026")
    folder = ROOT / config["report_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    snapshot.save_html(str(folder / "drift.html"))
    payload = json.loads(snapshot.json())
    save_json(folder / "drift.json", payload)
    export_variables(payload, config).to_csv(folder / "drift_variables.csv", index=False)
    save_json(folder / "calidad.json", {"full_data_checks": quality, "sampling": samples,
                                       "historical_data_version": manifest["historical_data_version"],
                                       "raw_source_observations": "Consultar datos_resumen.json: exclusiones, catálogo y estación sin actividad."})
    save_json(folder / "entorno.json", {"evidently": version("evidently"), "pandas": version("pandas"),
                                       "numpy": version("numpy"), "pyarrow": version("pyarrow"),
                                       "isolated_from_training": True})
    print(json.dumps({"report": "reports/etapa5/drift.html", "sample_rows": samples}))


if __name__ == "__main__":
    args = parser(__doc__).parse_args()
    generate(load_config(args.config))
