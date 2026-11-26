"""Predicciones trazables de A para monitoreo, sin entrenar ni promover modelos."""

import argparse
import json
import sys
from pathlib import Path
from importlib.metadata import version

import numpy as np

from .common import ROOT, load_config, model_input, save_json, sha256, verified_dataset


def generate(model_dir, output_dir):
    from mibici_equipo39.serving.model_loader import load_model, verify_bundle

    if not sys.dont_write_bytecode:
        raise ValueError("Ejecute python -B para preservar el paquete verificado.")
    config = load_config()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    loaded = load_model(model_dir, ROOT / "references/etapa4/model_manifest.json")
    if (loaded.manifest["model_version"] != config["expected_a_version"]
            or loaded.manifest["source_run_id"] != config["expected_a_run"]):
        raise ValueError("El paquete no es la versión A fijada en el protocolo.")
    manifest = {"protocol_sha256": config["protocol_sha256"],
                "model_name": loaded.manifest["model_name"],
                "model_version": loaded.manifest["model_version"],
                "source_run_id": loaded.manifest["source_run_id"],
                "bundle_sha256": loaded.manifest["bundle_sha256"], "files": {},
                "environment": {name:version(name) for name in ("mlflow", "scikit-learn", "pandas", "numpy", "pyarrow")},
                "code_sha256":sha256(Path(__file__))}
    for name in ("reference", "current"):
        frame, source = verified_dataset(name, config)
        values = []
        for start in range(0, len(frame), 100000):
            batch = frame.iloc[start:start + 100000]
            pred = np.asarray(loaded.predict(model_input(batch, config)), dtype=float).reshape(-1)
            if len(pred) != len(batch) or not np.isfinite(pred).all() or (pred < 0).any():
                raise ValueError("Predicciones incompletas o inválidas.")
            values.append(pred)
        result = frame[["station_id", "prediction_time", "target_departures"]].copy()
        result["prediction_a"] = np.concatenate(values)
        path = output / f"{name}_predictions.parquet"
        result.to_parquet(path, index=False)
        manifest["files"][name] = {"file": path.name, "sha256": sha256(path),
                                   "data_sha256": source["files"][name]["sha256"], "rows": len(result)}
    verify_bundle(model_dir, loaded.manifest)
    save_json(output / "manifest.json", manifest)
    print(json.dumps({"model_version": manifest["model_version"], "rows": {k:v["rows"] for k,v in manifest["files"].items()}}))


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--model-dir", default=str(ROOT / "models/serving/p1"))
    cli.add_argument("--output-dir", default=str(ROOT / "private_results/etapa5/seasonal"))
    args = cli.parse_args()
    generate(args.model_dir, args.output_dir)
