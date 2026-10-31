"""Explicación del hash del catálogo con un catálogo sintético; no lee los datos de MiBici."""

import importlib.util
import json
from pathlib import Path

import pandas as pd
import pytest

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "explain_station_hash", REPO / "scripts" / "explain_station_hash.py")
E = importlib.util.module_from_spec(spec)
spec.loader.exec_module(E)

LATITUDES = ["20.677224371110494", "20.702376291797922", "20.5"]


def test_each_rounding_gives_its_known_value():
    assert E.parse("20.677224371110494", single_rounding=True) == 20.677224371110498
    assert E.parse("20.677224371110494", single_rounding=False) == 20.67722437111049


@pytest.mark.parametrize("text, value", [("20", 20.0), ("20.5", 20.5), ("-103.25", -103.25)])
def test_simple_numbers_do_not_depend_on_the_rounding(text, value):
    assert E.parse(text, True) == E.parse(text, False) == value


def test_two_roundings_reproduce_a_manifest_made_on_x86(tmp_path):
    source = tmp_path / "data" / "external" / Path(C.STATIONS_URL).name
    source.parent.mkdir(parents=True)
    pd.DataFrame({"id": ["1", "2", "3"], "name": ["a", "b ", "c"], "latitude": LATITUDES,
                  "longitude": ["-103.5", "-103.25", "-103.75"], "dpcapacity": [10, 12, 14]}
                 ).to_csv(source, index=False)
    table, _, _ = D.clean_stations(source)
    table["latitude"] = E.emulate(pd.Series(LATITUDES, dtype="string"), single_rounding=False)
    (tmp_path / "references").mkdir()
    (tmp_path / "references" / "data_manifest.json").write_text(json.dumps({"outputs": {
        "processed/stations.parquet": {"logical_sha256": D.logical_hash(table, ["station_id"])}}}))

    result = E.explain(tmp_path)

    assert result["emulations"]["dos_redondeos"]["matches_manifest_hash"] is True
    assert result["emulations"]["un_redondeo"]["matches_manifest_hash"] is False
    assert result["differences_between_emulations"]["latitude"]["rows"] == 1
    assert result["differences_between_emulations"]["longitude"]["rows"] == 0
