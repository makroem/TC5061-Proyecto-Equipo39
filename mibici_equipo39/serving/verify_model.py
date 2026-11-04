"""Compara P1 local con la misma versión del Registry en un proceso independiente."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import mlflow.sklearn
import numpy as np
import pandas as pd

from mibici_equipo39.serving.model_loader import load_model, verify_bundle
from mibici_equipo39.serving.settings import DEFAULT_MANIFEST, DEFAULT_MODEL_DIR

REFERENCE_SCRIPT = """
import json, sys
import mlflow.pyfunc
import pandas as pd
from pathlib import Path
spec = json.loads(Path(sys.argv[2]).read_text(encoding='utf-8'))
frame = pd.DataFrame(spec['rows']).astype(spec['dtypes'])
model = mlflow.pyfunc.load_model(sys.argv[1])
pred = model.predict(frame)
Path(sys.argv[3]).write_text(json.dumps([float(x) for x in pred]), encoding='utf-8')
"""


def make_inputs(profile):
    """Casos artificiales de calendario, sin viajes ni información de usuarios."""
    if profile == "basic":
        stations, months, days = ("10", "20", "99999"), (6,), (5,)
    elif profile == "extended":
        stations, months, days = ("10", "20", "50", "100", "200", "99999"), range(1, 13), range(7)
    else:
        raise ValueError("Perfil de comprobación no reconocido.")
    rows = [{"station_id": station, "hour_of_day": hour, "day_of_week": day,
             "month": month, "is_weekend": int(day >= 5),
             "hour_sin": float(np.sin(2 * np.pi * hour / 24)),
             "hour_cos": float(np.cos(2 * np.pi * hour / 24)),
             "month_sin": float(np.sin(2 * np.pi * month / 12)),
             "month_cos": float(np.cos(2 * np.pi * month / 12))}
            for station in stations for month in months for day in days for hour in range(24)]
    types = {"station_id": "object", "hour_of_day": "int32", "day_of_week": "int32",
             "month": "int32", "is_weekend": "int64", "hour_sin": "float64",
             "hour_cos": "float64", "month_sin": "float64", "month_cos": "float64"}
    return rows, types, pd.DataFrame(rows).astype(types)


def check_station_sample(model, stations):
    """Confirma el origen conocido o desconocido en las tablas del baseline P1."""
    if not hasattr(model, "means_") or not model.means_:
        raise ValueError("El perfil ampliado requiere las tablas del baseline P1 seleccionado.")
    known = set(model.means_[0].index.get_level_values("station_id").astype(str))
    selected_known = set(stations) - {"99999"}
    if not selected_known.issubset(known) or "99999" in known:
        raise ValueError("Las estaciones del ensayo no corresponden a los casos conocidos y de respaldo.")
    return {"known_station_ids": sorted(selected_known, key=int),
            "unknown_station_ids": ["99999"], "known_stations_in_model": len(known)}


def verify(model_dir, manifest_path, report_path, profile="basic"):
    """Compara el perfil básico (72 filas) o el ampliado (12096) sin reentrenar."""
    if not os.environ.get("MLFLOW_TRACKING_URI"):
        raise ValueError("Configure el tracking oficial antes de comparar.")
    # Evita archivos de bytecode en el paquete verificado, también en el proceso hijo.
    if not sys.dont_write_bytecode:
        raise ValueError("Ejecute python -B para conservar el paquete sin archivos de bytecode.")
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    rows, types, frame = make_inputs(profile)
    station_sample = None
    with patch("requests.sessions.Session.request", side_effect=RuntimeError("Red deshabilitada")):
        loaded = load_model(model_dir, manifest_path)
        if profile == "extended":
            # El cargador ya verificó la firma y todas las huellas antes de deserializar.
            raw_model = mlflow.sklearn.load_model(str(Path(model_dir).resolve()))
            station_sample = check_station_sample(raw_model, frame["station_id"].unique())
        local = np.asarray(loaded.predict(frame), dtype=float)
        repeated = np.asarray(loaded.predict(frame), dtype=float)
    manifest = loaded.manifest
    uri = f"models:/{manifest['model_name']}/{manifest['model_version']}"
    with tempfile.TemporaryDirectory(prefix="paridad-", dir=report_path.parent) as temp:
        inputs, outputs = Path(temp) / "input.json", Path(temp) / "output.json"
        inputs.write_text(json.dumps({"rows": rows, "dtypes": types}), encoding="utf-8")
        child_env = os.environ.copy()
        child_env["PYTHONDONTWRITEBYTECODE"] = "1"
        child_env.pop("PYTHONPATH", None)
        # Código fijo, intérprete actual y versión validada; no usa shell ni comandos de una petición.
        result = subprocess.run(  # nosec B603
            [sys.executable, "-I", "-B", "-c", REFERENCE_SCRIPT, uri, str(inputs.resolve()),
             str(outputs.resolve())], cwd=temp, env=child_env, capture_output=True, text=True,
            timeout=180, check=False,
        )
        if result.returncode:
            raise RuntimeError("Falló la predicción independiente desde el Registry.")
        reference = np.asarray(json.loads(outputs.read_text(encoding="utf-8")), dtype=float)
    if local.shape != (len(rows),) or reference.shape != local.shape:
        raise ValueError("Cantidad de predicciones inesperada.")
    if not np.isfinite(local).all() or (local < 0).any():
        raise ValueError("Predicción no finita o negativa.")
    np.testing.assert_allclose(local, reference, rtol=0, atol=1e-12)
    np.testing.assert_array_equal(local, repeated)
    verify_bundle(model_dir, manifest)
    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(), "responsible": "Marco",
        "model_name": manifest["model_name"], "model_version": manifest["model_version"],
        "source_run_id": manifest["source_run_id"], "bundle_sha256": manifest["bundle_sha256"],
        "profile": profile,
        "rows": len(rows), "reference_process": "isolated_python_registry_numeric_version",
        "calendar_coverage": {"months": sorted(frame["month"].unique().tolist()),
                              "days_of_week": sorted(frame["day_of_week"].unique().tolist()),
                              "hours": sorted(frame["hour_of_day"].unique().tolist())},
        "station_sample": station_sample,
        "max_absolute_difference": float(np.max(np.abs(local - reference))),
        "repeat_predictions_equal": True, "local_requests_network_disabled": True,
        "bundle_unchanged_after_load": True, "scope": "Windows Python; no prueba de API o contenedor",
    }
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report-path", type=Path)
    parser.add_argument("--profile", choices=("basic", "extended"), default="basic")
    args = vars(parser.parse_args())
    if args["report_path"] is None:
        name = "paridad_modelo_ampliada_marco.json" if args["profile"] == "extended" else "paridad_modelo_marco.json"
        args["report_path"] = Path("reports/etapa4") / name
    verify(**args)


if __name__ == "__main__":
    main()
