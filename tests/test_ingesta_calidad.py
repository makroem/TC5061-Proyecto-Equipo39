"""Límites de ingesta con datos sintéticos; no consultan servicios externos."""

import sqlite3
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
import requests

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D


@pytest.fixture
def dedup_db():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE seen (trip_id TEXT PRIMARY KEY, payload_hash TEXT)")
    yield db
    db.close()


def trip(**changes):
    row = {"trip_id": "1", "origin_id": "2", "destination_id": "3",
           "started_at": "2025-10-01 00:00:00", "ended_at": "2025-10-01 00:15:00"}
    row.update(changes)
    return pd.DataFrame([row], dtype="string")


@pytest.mark.parametrize("changes,reason,departures", [
    ({"trip_id": " "}, "missing_trip_id", 0),
    ({"started_at": "no-fecha"}, "invalid_start", 0),
    ({"started_at": "2025-09-30 23:59:59"}, "outside_range", 0),
    ({"started_at": "2026-10-01 00:00:00"}, "outside_range", 0),
    ({"origin_id": None}, "missing_station", 0),
    ({"destination_id": " "}, "missing_station", 1),
    ({"ended_at": "no-fecha"}, "invalid_end", 1),
    ({"ended_at": "2025-09-30 23:59:59"}, "end_before_start", 1),
])
def test_exclusions_preserve_available_departures(dedup_db, changes, reason, departures):
    complete, dep, arr, counts = D.clean_trips(trip(**changes), dedup_db)
    assert complete.empty and arr.empty
    assert len(dep) == departures
    assert counts[reason] == 1
    assert sum(v for k, v in counts.items() if k != "raw_rows") == 1


def test_start_boundary_zero_duration_and_trimmed_ids_are_valid(dedup_db):
    complete, dep, arr, counts = D.clean_trips(
        trip(trip_id=" 1 ", origin_id=" 2 ", ended_at="2025-10-01 00:00:00"), dedup_db)
    assert counts["retained_rows"] == len(dep) == len(arr) == 1
    assert complete.iloc[0].trip_id == "1"
    assert dep.iloc[0].station_id == "2"


def test_repeated_ids_between_chunks_do_not_duplicate_events(dedup_db):
    first = trip()
    D.clean_trips(first, dedup_db)
    complete, dep, arr, counts = D.clean_trips(first, dedup_db)
    assert complete.empty and dep.empty and arr.empty
    assert counts["duplicates"] == 1


def test_conflicting_ids_inside_one_chunk_are_rejected(dedup_db):
    with pytest.raises(ValueError, match="dentro del bloque"):
        D.clean_trips(pd.concat([trip(), trip(destination_id="4")]), dedup_db)


@pytest.mark.parametrize("encoding,separator", [
    ("utf-8", ","), ("utf-8-sig", ";"), ("cp1252", ";"),
])
def test_csv_encoding_and_separator_preserve_station_names(tmp_path, encoding, separator):
    path = tmp_path / "stations.csv"
    text = separator.join(["id", "name", "latitude", "longitude", "dpcapacity"]) + "\n"
    text += separator.join(["2", "Estación Niñez", "20.6", "-103.3", "20"]) + "\n"
    path.write_bytes(text.encode(encoding))
    stations, detected, sep = D.clean_stations(path)
    assert stations.iloc[0].station_name == "Estación Niñez"
    assert sep == separator
    assert detected == ("cp1252" if encoding == "cp1252" else "utf-8-sig")
    assert stations.iloc[0].valid_capacity and stations.iloc[0].valid_coordinates


def test_column_names_normalize_accents_and_spaces():
    assert D.column_name("  INÍCIO DEL VIAJE  ") == "inicio_del_viaje"


@pytest.mark.parametrize("ids", [["1", "1"], ["1", " "], ["1", None]])
def test_station_ids_must_be_present_and_unique(tmp_path, ids):
    path = tmp_path / "stations.csv"
    pd.DataFrame({"id": ids, "name": ["A", "B"], "latitude": [20, 20],
                  "longitude": [-103, -103], "dpcapacity": [20, 20]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="IDs ausentes o repetidos"):
        D.clean_stations(path)


def test_station_schema_is_required(tmp_path):
    path = tmp_path / "stations.csv"
    path.write_text("id,name\n1,A\n", encoding="utf-8")
    with pytest.raises(ValueError, match="columnas requeridas"):
        D.clean_stations(path)


def test_invalid_capacity_and_coordinates_are_flagged(tmp_path):
    path = tmp_path / "stations.csv"
    pd.DataFrame({"id": ["1", "2", "3"], "name": ["A", "B", "C"],
                  "latitude": [91, 20, "error"], "longitude": [-103, 181, -103],
                  "dpcapacity": [0, 1.5, "error"]}).to_csv(path, index=False)
    stations, _, _ = D.clean_stations(path)
    assert not stations.valid_capacity.any()
    assert not stations.valid_coordinates.any()


def test_logical_hash_ignores_row_order_but_detects_changed_values():
    frame = pd.DataFrame({"station_id": ["1", "2"], "count": [2, 3]})
    original = D.logical_hash(frame, ["station_id"])
    assert original == D.logical_hash(frame.iloc[::-1], ["station_id"])
    frame.loc[0, "count"] += 1
    assert original != D.logical_hash(frame, ["station_id"])


def test_parquet_output_and_manifest_counts_agree(tmp_path):
    frame = pd.DataFrame({"trip_id": ["2", "1"], "origin_id": ["3", "4"]})
    hashes = {}
    relative = Path("processed/trips/part-00000.parquet")
    D.write_part(frame, tmp_path, relative, ["trip_id"], hashes)
    saved = pd.read_parquet(tmp_path / relative)
    assert saved.trip_id.tolist() == ["1", "2"]
    assert hashes[relative.as_posix()] == {
        "rows": 2, "logical_sha256": D.logical_hash(saved, ["trip_id"])}


@pytest.mark.parametrize("interrupted", [False, True])
def test_http_failure_never_publishes_partial_download(tmp_path, monkeypatch, interrupted):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def raise_for_status(self):
            if not interrupted:
                raise requests.HTTPError("503 synthetic")

        def iter_content(self, block_size):
            yield b"id,name\n1,"
            raise requests.ConnectionError("synthetic connection interrupted")

    def get(*args, **kwargs):
        calls.append(kwargs)
        return Response()

    monkeypatch.setattr(D.requests, "get", get)
    monkeypatch.setattr(D.time, "sleep", lambda _: None)
    path = tmp_path / "download.csv"
    with pytest.raises(RuntimeError, match="No se pudo descargar"):
        D.download_file("https://example.invalid/trips.csv", path)
    assert len(calls) == 3
    assert all(call["timeout"] == (10, 120) for call in calls)
    assert not path.exists() and not path.with_suffix(".csv.part").exists()


def test_ingestion_without_manifest_stops_before_download(tmp_path, monkeypatch):
    for key in ["RAW", "EXTERNAL", "REFERENCES", "REPORTS"]:
        monkeypatch.setattr(C, key, tmp_path / key.lower())

    def forbidden(*args, **kwargs):
        pytest.fail("No debe descargarse nada sin el manifiesto confirmado")

    monkeypatch.setattr(D, "download_file", forbidden)
    with pytest.raises(FileNotFoundError, match="data_manifest.json"):
        D.ingest("verify")


@pytest.fixture
def annual_sources(tmp_path, monkeypatch):
    paths = {"ROOT": tmp_path, "DATA": tmp_path / "data",
             "RAW": tmp_path / "data/raw", "EXTERNAL": tmp_path / "data/external",
             "PROCESSED": tmp_path / "data/processed", "INTERIM": tmp_path / "data/interim",
             "REFERENCES": tmp_path / "references", "REPORTS": tmp_path / "reports"}
    for key, path in paths.items():
        monkeypatch.setattr(C, key, path)
        path.mkdir(parents=True, exist_ok=True)
    catalog = C.EXTERNAL / Path(C.STATIONS_URL).name
    catalog.write_text("id,name,latitude,longitude,dpcapacity\n2,Dos,20,-103,20\n", encoding="utf-8")
    for number, (month, url) in enumerate(C.SOURCE_URLS.items()):
        frame = pd.DataFrame({" Viaje Íd ": [str(number)],
                              "Inicio del viaje": [month + "-01 10:00:00"],
                              "Fin del viaje": [month + "-01 10:15:00"],
                              "Origen Id": ["2"], "Destino Id": ["2"]})
        frame.to_csv(C.RAW / Path(url).name, index=False, sep=";", encoding="utf-8-sig")
    def forbidden(*args, **kwargs):
        pytest.fail("Los archivos sintéticos locales no deben iniciar conexiones")
    monkeypatch.setattr(D.requests, "get", forbidden)
    return C.RAW / Path(next(iter(C.SOURCE_URLS.values()))).name


def test_missing_trip_column_stops_ingestion(annual_sources):
    frame = pd.read_csv(annual_sources, sep=";")
    frame.drop(columns="Destino Id").to_csv(annual_sources, index=False, sep=";")
    with pytest.raises(ValueError, match="Esquema de viajes inesperado"):
        D.ingest("freeze")


def test_changed_source_is_rejected_without_replacing_manifest(annual_sources):
    D.ingest("freeze")
    path = C.REFERENCES / "data_manifest.json"
    before = path.read_bytes()
    annual_sources.write_bytes(annual_sources.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="Hash distinto"):
        D.ingest("verify")
    assert path.read_bytes() == before


def test_logical_manifest_mismatch_preserves_confirmed_file(annual_sources):
    D.ingest("freeze")
    path = C.REFERENCES / "data_manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    next(iter(manifest["outputs"].values()))["rows"] += 1
    D.save_json(path, manifest)
    before = path.read_bytes()
    with pytest.raises(ValueError, match="no coincide con el manifiesto"):
        D.ingest("verify")
    assert path.read_bytes() == before


def test_cleanup_only_removes_a_child_of_data(tmp_path, monkeypatch):
    root = tmp_path / "data"
    child = root / "_build"
    child.mkdir(parents=True)
    (child / "temporary.txt").write_text("synthetic", encoding="utf-8")
    monkeypatch.setattr(C, "DATA", root)
    D.remove_data_directory(child)
    assert root.exists() and not child.exists()


@pytest.mark.integration
@pytest.mark.parametrize("optimized", [False, True])
def test_cleanup_rejects_root_and_outside_even_in_optimized_python(tmp_path, optimized):
    root = tmp_path / "data"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    sentinel = outside / "keep.txt"
    sentinel.write_text("keep", encoding="utf-8")
    code = """
import sys
from pathlib import Path
from mibici_equipo39 import config as C
from mibici_equipo39.dataset import remove_data_directory
C.DATA = Path(sys.argv[1])
for target in [C.DATA, Path(sys.argv[2])]:
    try:
        remove_data_directory(target)
    except ValueError:
        continue
    raise SystemExit('Unsafe directory was accepted')
"""
    result = subprocess.run([sys.executable, *(["-O"] if optimized else []),
                             "-c", code, str(root), str(outside)],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    assert root.is_dir() and sentinel.read_text(encoding="utf-8") == "keep"
