"""Descarga por bloques y verifica la identidad de los datos, sin publicar viajes."""

import argparse
import codecs
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time
import unicodedata

import pandas as pd
import requests

from . import config as C

# El portal rechaza el User-Agent predeterminado de python-requests con HTTP 406.
# Identificamos al cliente real; no se necesitan cookies ni automatizar un navegador.
DOWNLOAD_HEADERS = {"User-Agent": "MiBici-Equipo39/0.0.1 (academic data ingestion)"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sha_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8"
    )


def download_file(url, path, expected=None):
    """Reutiliza un archivo coincidente y nunca acepta un cambio silencioso."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if expected and sha_file(path) != expected:
            raise ValueError(f"Hash distinto en {path.name}; revisar antes de reemplazar.")
        return
    last_error = None
    part = path.with_suffix(path.suffix + ".part")
    for attempt in range(3):
        try:
            with requests.get(
                url, headers=DOWNLOAD_HEADERS, stream=True, timeout=(10, 120)
            ) as response:
                response.raise_for_status()
                with part.open("wb") as output:
                    for block in response.iter_content(1024 * 1024):
                        output.write(block)
            with part.open("rb") as stream:
                head = stream.read(250)
            if not part.stat().st_size or b"<html" in head.lower() or b"<!doctype" in head.lower():
                raise ValueError(f"No se recibió un CSV: {path.name}")
            if expected and sha_file(part) != expected:
                raise ValueError(f"La fuente cambió: {path.name}")
            part.replace(path)
            return
        except (requests.RequestException, OSError, ValueError) as exc:
            last_error = exc
            part.unlink(missing_ok=True)
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
    raise RuntimeError(f"No se pudo descargar {url}: {last_error}")


def csv_options(path):
    """Valida UTF8 completo; si falla usa CP1252 sin omitir caracteres."""
    encoding = "utf-8-sig"
    try:
        decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
        with Path(path).open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                decoder.decode(block)
        decoder.decode(b"", final=True)
    except UnicodeDecodeError:
        encoding = "cp1252"
    with Path(path).open(encoding=encoding, errors="strict") as stream:
        header = stream.readline()
    separator = ";" if header.count(";") > header.count(",") else ","
    return encoding, separator


def column_name(name):
    name = unicodedata.normalize("NFKD", name)
    name = "".join(x for x in name if not unicodedata.combining(x))
    return name.strip().lower().replace(" ", "_")


def clean_stations(path):
    encoding, separator = csv_options(path)
    frame = pd.read_csv(path, encoding=encoding, sep=separator, dtype="string")
    frame.columns = [column_name(x) for x in frame.columns]
    frame = frame.rename(
        columns={"id": "station_id", "name": "station_name", "dpcapacity": "capacity"}
    )
    columns = ["station_id", "station_name", "latitude", "longitude", "capacity"]
    if not set(columns).issubset(frame):
        raise ValueError("El catálogo no contiene las columnas requeridas.")
    frame = frame[columns].copy()
    frame.station_id = frame.station_id.str.strip()
    if (
        frame.station_id.isna().any()
        or frame.station_id.eq("").any()
        or frame.station_id.duplicated().any()
    ):
        raise ValueError("IDs ausentes o repetidos en catálogo.")
    for col in ["latitude", "longitude", "capacity"]:
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    frame["valid_capacity"] = frame.capacity.gt(0) & frame.capacity.mod(1).eq(0)
    frame["valid_coordinates"] = frame.latitude.between(-90, 90) & frame.longitude.between(
        -180, 180
    )
    return frame.sort_values("station_id").reset_index(drop=True), encoding, separator


def logical_hash(frame, keys):
    """Hash de valores normalizados en un orden explícito, independiente de Parquet."""
    ordered = frame.sort_values(keys).copy()
    text = ordered.to_csv(
        index=False, lineterminator="\n", date_format="%Y-%m-%d %H:%M:%S", na_rep=""
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def unique_chunk(frame, db):
    """Deduplica también entre bloques y meses; detecta un ID con datos distintos."""
    frame = frame.copy()
    normalized = frame.astype("string").fillna("")
    payload = normalized.iloc[:, 0]
    for column in normalized.columns[1:]:
        payload = payload.str.cat(normalized[column], sep="|")
    frame["payload_hash"] = payload.map(lambda x: hashlib.sha256(x.encode()).hexdigest())
    if frame.groupby("trip_id").payload_hash.nunique().gt(1).any():
        raise ValueError("Un trip_id tiene contenidos distintos dentro del bloque.")
    original = len(frame)
    frame = frame.drop_duplicates("trip_id").reset_index(drop=True)
    frame[["trip_id", "payload_hash"]].to_sql("staging", db, if_exists="replace", index=False)
    conflict = db.execute(
        "SELECT 1 FROM staging s JOIN seen v ON s.trip_id=v.trip_id WHERE s.payload_hash<>v.payload_hash LIMIT 1"
    ).fetchone()
    if conflict:
        raise ValueError("Un trip_id tiene contenidos distintos entre bloques o meses.")
    repeated = {
        x[0]
        for x in db.execute("SELECT s.trip_id FROM staging s JOIN seen v ON s.trip_id=v.trip_id")
    }
    fresh = frame.loc[~frame.trip_id.isin(repeated)].drop(columns="payload_hash")
    db.execute("INSERT OR IGNORE INTO seen SELECT * FROM staging")
    db.commit()
    return fresh, original - len(fresh)


def clean_trips(frame, db):
    """Devuelve viajes completos, salidas disponibles, llegadas coherentes y exclusiones."""
    counts = {"raw_rows": len(frame)}
    frame = frame.copy()
    for col in ["trip_id", "origin_id", "destination_id"]:
        frame[col] = frame[col].str.strip()
    bad_id = frame.trip_id.isna() | frame.trip_id.eq("")
    counts["missing_trip_id"] = int(bad_id.sum())
    frame, counts["duplicates"] = unique_chunk(frame.loc[~bad_id], db)
    for col in ["started_at", "ended_at"]:
        frame[col] = pd.to_datetime(frame[col], format="%Y-%m-%d %H:%M:%S", errors="coerce")
    departures = frame.loc[
        frame.started_at.notna() & frame.origin_id.notna() & frame.origin_id.ne("")
    ].copy()
    departures = departures.loc[
        departures.started_at.ge(C.SOURCE_START) & departures.started_at.lt(C.SOURCE_END_EXCLUSIVE)
    ]
    conditions = [
        ("invalid_start", frame.started_at.isna()),
        (
            "outside_range",
            frame.started_at.lt(C.SOURCE_START) | frame.started_at.ge(C.SOURCE_END_EXCLUSIVE),
        ),
        (
            "missing_station",
            frame.origin_id.isna()
            | frame.destination_id.isna()
            | frame.origin_id.eq("")
            | frame.destination_id.eq(""),
        ),
        ("invalid_end", frame.ended_at.isna()),
        ("end_before_start", frame.ended_at.lt(frame.started_at)),
    ]
    for reason, mask in conditions:
        mask = mask.reindex(frame.index).fillna(False)
        counts[reason] = int(mask.sum())
        frame = frame.loc[~mask]
    counts["retained_rows"] = len(frame)
    assert (
        sum(v for k, v in counts.items() if k not in ["raw_rows", "retained_rows"]) + len(frame)
        == counts["raw_rows"]
    )
    arrivals = frame.copy()
    dep = departures[["trip_id", "origin_id", "started_at"]].rename(
        columns={"origin_id": "station_id", "started_at": "timestamp"}
    )
    arr = arrivals[["trip_id", "destination_id", "ended_at"]].rename(
        columns={"destination_id": "station_id", "ended_at": "timestamp"}
    )
    return frame, dep, arr, counts


def write_part(frame, build, relative, keys, output_hashes):
    path = build / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    frame = frame.sort_values(keys).reset_index(drop=True)
    frame.to_parquet(path, index=False, compression="snappy")
    output_hashes[relative.as_posix()] = {
        "rows": len(frame),
        "logical_sha256": logical_hash(frame, keys),
    }


def ingest(mode):
    """Reconstruye el periodo completo y acepta una versión nueva solo en freeze."""
    for path in [C.RAW, C.EXTERNAL, C.REFERENCES, C.REPORTS]:
        path.mkdir(parents=True, exist_ok=True)
    manifest_path = C.REFERENCES / "data_manifest.json"
    previous = (
        json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    )
    if mode == "verify" and previous is None:
        raise FileNotFoundError("Falta data_manifest.json; Persona1 debe congelarlo en su PR.")
    expected = (
        {x["url"]: x["sha256"] for x in previous["sources"]}
        if previous and mode == "verify"
        else {}
    )
    months = (
        pd.period_range(
            C.SOURCE_START, pd.Timestamp(C.SOURCE_END_EXCLUSIVE) - pd.Timedelta(days=1), freq="M"
        )
        .astype(str)
        .tolist()
    )
    if sorted(C.SOURCE_URLS) != months:
        raise ValueError("Las URLs no corresponden exactamente a los doce meses configurados.")
    station_path = C.EXTERNAL / Path(C.STATIONS_URL).name
    download_file(C.STATIONS_URL, station_path, expected.get(C.STATIONS_URL))
    stations, encoding, separator = clean_stations(station_path)
    build = C.DATA / "_build"
    if build.exists():
        assert build.resolve().is_relative_to(C.DATA.resolve())
        shutil.rmtree(build)
    build.mkdir()
    hashes, sources, rows = {}, [], []
    write_part(stations, build, Path("processed/stations.parquet"), ["station_id"], hashes)
    sources.append(
        {
            "url": C.STATIONS_URL,
            "name": station_path.name,
            "sha256": sha_file(station_path),
            "bytes": station_path.stat().st_size,
            "rows": len(stations),
            "encoding": encoding,
            "separator": separator,
        }
    )
    db = sqlite3.connect(build / "dedup.sqlite")
    db.execute("CREATE TABLE seen (trip_id TEXT PRIMARY KEY, payload_hash TEXT)")
    origins, destinations = set(), set()
    known_ids = set(stations.station_id)
    for month, url in sorted(C.SOURCE_URLS.items()):
        path = C.RAW / Path(url).name
        download_file(url, path, expected.get(url))
        encoding, separator = csv_options(path)
        header = pd.read_csv(path, encoding=encoding, sep=separator, nrows=0).columns
        names = {x: column_name(x) for x in header}
        aliases = {
            "viaje_id": "trip_id",
            "inicio_del_viaje": "started_at",
            "fin_del_viaje": "ended_at",
            "origen_id": "origin_id",
            "destino_id": "destination_id",
        }
        selected = {x: aliases[y] for x, y in names.items() if y in aliases}
        if set(selected.values()) != set(aliases.values()):
            raise ValueError(f"Esquema de viajes inesperado en {month}.")
        total = {
            "month": month,
            "unknown_departures": 0,
            "unknown_arrivals": 0,
            "departure_rows": 0,
            "arrival_rows": 0,
        }
        for number, frame in enumerate(
            pd.read_csv(
                path,
                encoding=encoding,
                sep=separator,
                usecols=list(selected),
                dtype="string",
                chunksize=C.CHUNKSIZE,
            )
        ):
            frame = frame.rename(columns=selected)[list(aliases.values())]
            trips, dep, arr, counts = clean_trips(frame, db)
            for key, value in counts.items():
                total[key] = total.get(key, 0) + value
            origins.update(dep.station_id)
            destinations.update(arr.station_id)
            total["unknown_departures"] += int((~dep.station_id.isin(known_ids)).sum())
            total["unknown_arrivals"] += int((~arr.station_id.isin(known_ids)).sum())
            total["departure_rows"] += len(dep)
            total["arrival_rows"] += len(arr)
            for kind, data in [
                ("processed/trips", trips),
                ("interim/departures", dep),
                ("interim/arrivals", arr),
            ]:
                relative = Path(kind) / f"month={month}" / f"part-{number:05d}.parquet"
                write_part(data, build, relative, ["trip_id"], hashes)
        rows.append(total)
        sources.append(
            {
                "month": month,
                "url": url,
                "name": path.name,
                "sha256": sha_file(path),
                "bytes": path.stat().st_size,
                "encoding": encoding,
                "separator": separator,
                "counts": total,
            }
        )
        print(month, "viajes válidos:", total["retained_rows"], flush=True)
    db.close()
    version_inputs = {
        "source_start": C.SOURCE_START,
        "source_end_exclusive": C.SOURCE_END_EXCLUSIVE,
        "cleaning_schema_version": C.CLEANING_SCHEMA_VERSION,
        "chunksize": C.CHUNKSIZE,
        "sources": [{"url": x["url"], "sha256": x["sha256"]} for x in sources],
    }
    manifest = {
        **version_inputs,
        "sources": sources,
        "data_version": digest(version_inputs),
        "outputs": hashes,
    }
    if mode == "verify" and manifest != previous:
        raise ValueError(
            "La reconstrucción no coincide con el manifiesto; no se modificó el original."
        )
    for folder in ["processed", "interim"]:
        destination = C.DATA / folder
        if destination.exists():
            assert destination.resolve().is_relative_to(C.DATA.resolve())
            shutil.rmtree(destination)
        shutil.move(str(build / folder), str(destination))
    shutil.rmtree(build)
    if mode == "freeze":
        save_json(manifest_path, manifest)
    quality = {
        "months": len(months),
        "data_version": manifest["data_version"],
        "raw_rows": sum(x["raw_rows"] for x in rows),
        "retained_rows": sum(x["retained_rows"] for x in rows),
        "catalog_rows": len(stations),
        "valid_capacity_stations": int(stations.valid_capacity.sum()),
        "origin_stations": len(origins),
        "destination_stations": len(destinations),
        "union_stations": len(origins | destinations),
        "source_bytes": sum(x["bytes"] for x in sources),
    }
    save_json(C.REPORTS / "calidad_datos.json", quality)
    pd.DataFrame(rows).to_csv(C.REPORTS / "calidad_datos_por_mes.csv", index=False)
    print(json.dumps(quality, indent=2), flush=True)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--freeze-manifest", action="store_true")
    group.add_argument("--verify-manifest", action="store_true")
    args = parser.parse_args()
    ingest("freeze" if args.freeze_manifest else "verify")


if __name__ == "__main__":
    main()
