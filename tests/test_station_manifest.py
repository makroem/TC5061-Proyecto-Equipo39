"""Diagnostico del catalogo con fuentes sinteticas y sin alterar el manifiesto."""

import json
from pathlib import Path
import sys

import pandas as pd
import pytest

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D
from scripts.check_station_manifest import inspect, main, table_summary


@pytest.fixture
def station_project(tmp_path):
    source = tmp_path / "data/external" / Path(C.STATIONS_URL).name
    source.parent.mkdir(parents=True)
    source.write_text(
        "id,name,latitude,longitude,dpcapacity\n"
        "2, Estacion dos ,20.6,-103.3,20\n"
        "1,Estacion uno,20.7,-103.4,24\n", encoding="utf-8"
    )
    frame, _, _ = D.clean_stations(source)
    target = tmp_path / "data/processed/stations.parquet"
    target.parent.mkdir(parents=True)
    frame.to_parquet(target, index=False)
    D.save_json(tmp_path / "references/data_manifest.json", {
        "data_version": "fixture", "sources": [{"name": source.name, "sha256": D.sha_file(source)}],
        "outputs": {"processed/stations.parquet": {
            "rows": len(frame), "logical_sha256": D.logical_hash(frame, ["station_id"])
        }},
    })
    return tmp_path


def test_station_check_preserves_files_and_reports_matching_outputs(station_project):
    files = list(station_project.rglob("*.*"))
    before = {p: p.read_bytes() for p in files}
    result = inspect(station_project, verify_outputs=True)
    assert result["status"] == "PASS"
    assert result["outputs"] == {"performed": True, "checked": 1, "mismatches": []}
    assert result["tables"]["stored"]["names_with_outer_spaces"] == 1
    assert before == {p: p.read_bytes() for p in files}
    assert "Estacion uno" not in json.dumps(result)


def test_changed_station_value_is_detected_without_updating_manifest(station_project):
    target = station_project / "data/processed/stations.parquet"
    frame = pd.read_parquet(target)
    frame.loc[0, "latitude"] += 0.01
    frame.to_parquet(target, index=False)
    result = inspect(station_project, verify_outputs=True)
    assert result["status"] == "FAIL"
    assert not result["checks"]["stored_matches_manifest"]
    assert result["checks"]["rebuilt_matches_manifest"]
    assert len(result["outputs"]["mismatches"]) == 1


def test_missing_manifest_output_is_reported(station_project):
    path = station_project / "references/data_manifest.json"
    manifest = json.loads(path.read_text("utf-8"))
    manifest["outputs"]["interim/departures/missing.parquet"] = {
        "rows": 1, "logical_sha256": "absent"
    }
    D.save_json(path, manifest)
    result = inspect(station_project, verify_outputs=True)
    assert result["status"] == "FAIL"
    assert result["outputs"]["mismatches"][0]["reason"] == "missing"


def test_source_change_fails_even_if_processed_values_are_equal(station_project):
    source = station_project / "data/external" / Path(C.STATIONS_URL).name
    source.write_bytes(source.read_bytes() + b"\n")
    result = inspect(station_project)
    assert result["status"] == "FAIL"
    assert not result["checks"]["source_sha256_matches"]
    assert result["checks"]["stored_equals_rebuilt"]


def test_column_hashes_ignore_row_order_and_detect_name_spaces(station_project):
    frame = pd.read_parquet(station_project / "data/processed/stations.parquet")
    before = table_summary(frame)
    assert table_summary(frame.iloc[::-1]) == before
    frame["station_name"] = frame.station_name.str.strip()
    after = table_summary(frame)
    assert before["logical_sha256"] != after["logical_sha256"]
    assert before["columns"]["station_name"] != after["columns"]["station_name"]
    assert before["columns"]["latitude"] == after["columns"]["latitude"]


def test_cli_refuses_to_overwrite_an_input(station_project, monkeypatch):
    source = station_project / "data/external" / Path(C.STATIONS_URL).name
    before = source.read_bytes()
    monkeypatch.setattr(sys, "argv", ["check_station_manifest.py", "--project-root",
                                     str(station_project), "--output", str(source)])
    with pytest.raises(FileExistsError):
        main()
    assert source.read_bytes() == before
