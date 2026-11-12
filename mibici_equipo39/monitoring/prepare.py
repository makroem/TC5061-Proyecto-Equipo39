"""Prepara referencia, entrenamiento B y octubre sin alterar data/processed."""

import json
import sqlite3
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from mibici_equipo39.dataset import clean_stations, clean_trips, column_name, csv_options, download_file, logical_hash
from mibici_equipo39.features import add_calendar_features, eligible_stations
from .common import ROOT, load_config, parser, save_json, sha256, validate_frame


def calendar_frame(keys):
    return add_calendar_features(keys.rename(columns={"prediction_time": "hour"})).rename(columns={"hour": "prediction_time"})


def historical_tables(data_dir, config):
    """Comprueba las salidas contra el manifiesto confirmado y reconstruye los conteos."""
    manifest = json.loads((ROOT / "references/data_manifest.json").read_text(encoding="utf-8"))
    if manifest["data_version"] != config["historical_data_version"]:
        raise ValueError("La versión histórica no es la que utilizó A.")
    meta = pd.read_parquet(data_dir / "processed/metadata.parquet")
    y = pd.read_parquet(data_dir / "processed/y_p1.parquet")["target_departures"]
    if len(meta) != len(y) or not meta.data_version.eq(manifest["data_version"]).all():
        raise ValueError("Metadata y objetivo históricos no coinciden.")
    counts = []
    checked = 0
    for relative, expected in manifest["outputs"].items():
        if not relative.startswith("interim/departures/"):
            continue
        part = pd.read_parquet(data_dir / relative)
        if len(part) != expected["rows"] or logical_hash(part, ["trip_id"]) != expected["logical_sha256"]:
            raise ValueError(f"La partición histórica no coincide: {relative}.")
        checked += 1
        part["prediction_time"] = pd.to_datetime(part.timestamp).dt.floor("h")
        counts.append(part.groupby(["station_id", "prediction_time"], observed=True).size())
    if not counts:
        raise ValueError("No se encontraron salidas históricas versionadas.")
    counts = pd.concat(counts).groupby(level=[0, 1], observed=True).sum()
    expected_y = counts.reindex(pd.MultiIndex.from_frame(meta[["station_id", "prediction_time"]]), fill_value=0).to_numpy()
    if not np.array_equal(expected_y, y.to_numpy()):
        raise ValueError("Los objetivos históricos difieren de las salidas verificadas.")
    expected_train = meta.prediction_time.ge(config["reference_start"]) & meta.prediction_time.lt(config["reference_end"])
    if not np.array_equal(meta.split.eq("train"), expected_train):
        raise ValueError("Train histórico no coincide con la referencia de A.")
    cohort = eligible_stations(meta, y, min_departures=config["minimum_training_departures"])
    mask = meta.station_id.isin(cohort)
    frame = calendar_frame(meta.loc[mask, ["station_id", "prediction_time"]].reset_index(drop=True))
    frame["target_departures"] = y.loc[mask].to_numpy()
    frame = frame.sort_values(["station_id", "prediction_time"]).reset_index(drop=True)
    return frame, cohort, checked


def current_departures(path, config):
    """Lee solo columnas operativas; no incorpora datos personales a las tablas."""
    mapping = {"viaje_id": "trip_id", "inicio_del_viaje": "started_at", "fin_del_viaje": "ended_at",
               "origen_id": "origin_id", "destino_id": "destination_id"}
    encoding, separator = csv_options(path)
    header = pd.read_csv(path, encoding=encoding, sep=separator, nrows=0)
    columns = [c for c in header.columns if column_name(c) in mapping]
    if len(columns) != 5:
        raise ValueError("El CSV no tiene las cinco columnas operativas esperadas.")
    counts = Counter()
    parts = []
    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE seen (trip_id TEXT PRIMARY KEY, payload_hash TEXT)")
        for chunk in pd.read_csv(path, encoding=encoding, sep=separator, usecols=columns, dtype="string", chunksize=100000):
            chunk.columns = [mapping[column_name(c)] for c in chunk.columns]
            _, dep, _, summary = clean_trips(chunk, db, config["current_start"], config["current_end"])
            parts.append(dep[["station_id", "timestamp"]])
            counts.update(summary)
    departures = pd.concat(parts, ignore_index=True)
    expected_days = pd.date_range(config["current_start"], config["current_end"], inclusive="left", freq="D")
    actual_days = pd.DatetimeIndex(departures.timestamp.dt.normalize().unique()).sort_values()
    if not expected_days.equals(actual_days):
        raise ValueError("Faltan días completos de salidas; no se rellenarán como demanda cero.")
    return departures, dict(counts)


def prepare(historical_data, config):
    folder = ROOT / config["data_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "references/etapa5/data_manifest.json"
    previous = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    sources = {}
    for kind in ("trips", "stations"):
        name = config[f"{kind}_url"].rsplit("/", 1)[1]
        path = folder / "raw" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        expected = previous.get("sources", {}).get(kind, {}).get("sha256")
        download_file(config[f"{kind}_url"], path, expected)
        sources[kind] = {"url": config[f"{kind}_url"], "file": name, "sha256": sha256(path), "bytes": path.stat().st_size}
    historical, cohort, checked = historical_tables(Path(historical_data), config)
    reference = historical.loc[historical.prediction_time.lt(config["reference_end"])].reset_index(drop=True)
    stations, _, _ = clean_stations(folder / "raw" / sources["stations"]["file"])
    departures, cleaning = current_departures(folder / "raw" / sources["trips"]["file"], config)
    usable = sorted(set(cohort) & set(stations.station_id))
    if not usable:
        raise ValueError("El catálogo actual no contiene estaciones de la cohorte de A.")
    hours = pd.date_range(config["current_start"], config["current_end"], freq="h", inclusive="left")
    keys = pd.MultiIndex.from_product([usable, hours], names=["station_id", "prediction_time"])
    counts = departures.assign(prediction_time=departures.timestamp.dt.floor("h")).groupby(["station_id", "prediction_time"], observed=True).size()
    current = calendar_frame(keys.to_frame(index=False))
    current["station_id"] = current.station_id.astype("string")
    current["target_departures"] = counts.reindex(keys, fill_value=0).to_numpy(dtype="int32")
    tables = {"reference": reference, "train_b": historical, "current": current}
    periods = {"reference": (config["reference_start"], config["reference_end"]),
               "train_b": (config["training_b_start"], config["training_b_end"]),
               "current": (config["current_start"], config["current_end"])}
    summaries, files = {}, {}
    for name, frame in tables.items():
        summaries[name] = validate_frame(frame, *periods[name], config)
        path = folder / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        files[name] = {"sha256": sha256(path), "rows": len(frame), "relative_path": path.relative_to(ROOT).as_posix()}
    summary = {"datasets": summaries, "cleaning_current": cleaning, "historical_departure_partitions_verified": checked,
               "cohort_from_a_train": len(cohort), "current_catalog_stations": len(stations),
               "cohort_absent_from_current_catalog": sorted(set(cohort) - set(usable)),
               "current_catalog_outside_a_cohort": len(set(stations.station_id) - set(cohort)),
               "current_departures_outside_cohort": int((~departures.station_id.isin(usable)).sum()),
               "current_departures_unknown_catalog": int((~departures.station_id.isin(stations.station_id)).sum()),
               "cohort_without_observed_current_departures": sorted(set(usable) - set(departures.station_id)),
               "zero_assumption": "Se asumen cero salidas en horas sin viaje de estaciones presentes en el catálogo. No hay inventario ni calendario de cierres; disponibilidad física no comprobada.",
               "source_completeness": "Se observaron salidas en cada día del mes; esto no demuestra ausencia de pérdidas parciales del proveedor."}
    manifest = {"protocol_sha256": config["protocol_sha256"], "historical_data_version": config["historical_data_version"],
                "sources": sources, "files": files, "cohort": cohort, "evaluation_cohort": usable,
                "historical_manifest_sha256": sha256(ROOT / "references/data_manifest.json")}
    save_json(manifest_path, manifest)
    save_json(ROOT / config["report_dir"] / "datos_resumen.json", summary)
    print(json.dumps(summaries, ensure_ascii=False))


def main():
    cli = parser(__doc__)
    cli.add_argument("--historical-data", default="data", help="Carpeta data obtenida por la ingesta histórica y features.")
    args = cli.parse_args()
    prepare(args.historical_data, load_config(args.config))


if __name__ == "__main__":
    main()
