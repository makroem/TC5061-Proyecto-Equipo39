"""Contratos compartidos para preparar, verificar y comparar el monitoreo."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = "references/etapa5/protocolo.json"


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path=DEFAULT_CONFIG):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    config = json.loads(path.read_text(encoding="utf-8"))
    periods = [pd.Timestamp(config[k]) for k in ("reference_start", "reference_end", "training_b_end", "current_start", "current_end")]
    if not periods[0] < periods[1] <= periods[2] <= periods[3] < periods[4]:
        raise ValueError("Las fechas permiten solapamiento o un periodo vacío.")
    if config["training_b_start"] != config["reference_start"]:
        raise ValueError("B debe ampliar la misma ventana histórica de A.")
    if config["automatic_promotion"]:
        raise ValueError("Este protocolo no permite promover modelos automáticamente.")
    # Git puede convertir LF a CRLF en Windows; la identidad no depende de ello.
    config["protocol_sha256"] = hashlib.sha256(path.read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()
    return config


def parser(description):
    result = argparse.ArgumentParser(description=description)
    result.add_argument("--config", default=DEFAULT_CONFIG)
    return result


def model_input(frame, config):
    result = frame[config["features"]].copy()
    result["station_id"] = result.station_id.astype(str)
    for column in ("hour_of_day", "day_of_week", "month"):
        result[column] = result[column].astype("int32")
    result["is_weekend"] = result.is_weekend.astype("int64")
    for column in config["numerical"]:
        result[column] = result[column].astype("float64")
    if result.isna().any().any():
        raise ValueError("Hay variables ausentes en la entrada.")
    return result


def validate_frame(frame, start, end, config):
    """Rechaza duplicados, fechas externas, etiquetas inválidas y calendario distinto."""
    keys = ["station_id", "prediction_time"]
    if frame.empty or frame[keys].isna().any().any() or frame.duplicated(keys).any():
        raise ValueError("Las claves deben existir y ser únicas.")
    times = pd.to_datetime(frame.prediction_time)
    if not (times.ge(start) & times.lt(end)).all():
        raise ValueError("Hay filas fuera del periodo permitido.")
    if not times.eq(times.dt.floor("h")).all():
        raise ValueError("La granularidad debe ser estación-hora.")
    y = frame.target_departures.to_numpy(dtype=float)
    if not np.isfinite(y).all() or (y < 0).any() or not np.equal(y, np.floor(y)).all():
        raise ValueError("La etiqueta debe ser un conteo finito y no negativo.")
    x = model_input(frame, config)
    expected = {"hour_of_day": times.dt.hour, "day_of_week": times.dt.dayofweek,
                "month": times.dt.month, "is_weekend": times.dt.dayofweek.ge(5).astype(int)}
    for column, values in expected.items():
        if not np.array_equal(x[column].to_numpy(), values.to_numpy()):
            raise ValueError(f"Calendario inconsistente: {column}.")
    for name, values in {"hour_sin": np.sin(2*np.pi*times.dt.hour/24),
                         "hour_cos": np.cos(2*np.pi*times.dt.hour/24),
                         "month_sin": np.sin(2*np.pi*times.dt.month/12),
                         "month_cos": np.cos(2*np.pi*times.dt.month/12)}.items():
        if not np.allclose(x[name], values, rtol=0, atol=1e-12):
            raise ValueError(f"Calendario cíclico inconsistente: {name}.")
    hours = len(pd.date_range(start, end, freq="h", inclusive="left"))
    if not frame.groupby("station_id", observed=True).size().eq(hours).all():
        raise ValueError("La malla no contiene todas las horas por estación.")
    return {"rows": len(frame), "stations": int(frame.station_id.nunique()),
            "days": int(times.dt.normalize().nunique()), "departures": int(y.sum()),
            "zero_share": float((y == 0).mean()), "missing_values": int(frame.isna().sum().sum()),
            "duplicate_keys": 0, "start": str(times.min()), "last_hour": str(times.max())}


def verified_dataset(name, config):
    manifest = json.loads((ROOT / "references/etapa5/data_manifest.json").read_text(encoding="utf-8"))
    if manifest["protocol_sha256"] != config["protocol_sha256"]:
        raise ValueError("El protocolo cambió después de preparar los datos.")
    path = ROOT / config["data_dir"] / f"{name}.parquet"
    if sha256(path) != manifest["files"][name]["sha256"]:
        raise ValueError(f"La huella de {name} no coincide con el manifiesto.")
    return pd.read_parquet(path), manifest
