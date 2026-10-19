import pytest

from mibici_equipo39.modeling import train


def test_controller_stops_when_tables_are_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(train, "REQUIRED", [tmp_path / "metadata.parquet"])
    monkeypatch.setattr(train.C, "ROOT", tmp_path)
    with pytest.raises(SystemExit, match="mibici_equipo39.features"):
        train.check_inputs(allow_dirty=True)


def test_controller_covers_p1_and_p2():
    assert train.QUESTIONS == ("P1", "P2")
