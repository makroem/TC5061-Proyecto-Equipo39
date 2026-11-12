"""Contratos de fecha, pares, remuestreo y limpieza del periodo nuevo."""

import sqlite3

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.dataset import clean_trips
from mibici_equipo39.monitoring.common import load_config, model_input, validate_frame
from mibici_equipo39.monitoring.metrics import block_bootstrap, improvement, metrics
from mibici_equipo39.monitoring.prepare import calendar_frame


@pytest.fixture
def current():
    frame = calendar_frame(pd.DataFrame({"station_id": "1", "prediction_time": pd.date_range("2026-10-01", "2026-11-01", inclusive="left", freq="h")}))
    frame["target_departures"] = 2
    return frame


def test_complete_grid_and_signature(current):
    c = load_config()
    assert validate_frame(current, c["current_start"], c["current_end"], c)["rows"] == 744
    x = model_input(current, c)
    assert list(x.columns) == c["features"]
    assert str(x.hour_of_day.dtype) == "int32"
    assert str(x.is_weekend.dtype) == "int64"


@pytest.mark.parametrize("fault", ["duplicate", "outside", "missing_hour", "calendar", "negative", "fraction", "infinity", "cyclic"])
def test_invalid_current_rejected(current, fault):
    c = load_config()
    if fault == "duplicate": current = pd.concat([current, current.iloc[:1]], ignore_index=True)
    if fault == "outside": current.loc[0, "prediction_time"] = pd.Timestamp("2026-09-30")
    if fault == "missing_hour": current = current.iloc[1:]
    if fault == "calendar": current.loc[0, "month"] = 9
    if fault == "negative": current.loc[0, "target_departures"] = -1
    if fault == "fraction": current["target_departures"] = 0.5
    if fault == "infinity": current["target_departures"] = np.inf
    if fault == "cyclic": current.loc[0, "hour_sin"] = 2.0
    with pytest.raises(ValueError): validate_frame(current, c["current_start"], c["current_end"], c)


def test_cleaning_accepts_new_period_without_changing_historical_default():
    frame = pd.DataFrame({"trip_id": ["1", "2"], "origin_id": ["1", "1"], "destination_id": ["2", "2"],
                          "started_at": ["2026-10-01 00:00:00", "2026-11-01 00:00:00"],
                          "ended_at": ["2026-10-01 00:10:00", "2026-11-01 00:10:00"]}, dtype="string")
    for custom, expected in [(True, 1), (False, 0)]:
        with sqlite3.connect(":memory:") as db:
            db.execute("CREATE TABLE seen (trip_id TEXT PRIMARY KEY, payload_hash TEXT)")
            kwargs = {"start": "2026-10-01", "end": "2026-11-01"} if custom else {}
            _, departures, _, _ = clean_trips(frame, db, **kwargs)
        assert len(departures) == expected


def test_mae_rmse_and_zero_baseline():
    assert metrics([1, 3], [0, 2]) == {"mae": 1.0, "rmse": 1.0}
    assert improvement(2, 1) == 50
    assert improvement(0, 1) is None


@pytest.mark.parametrize("prediction", [[1], [np.nan, 1], [np.inf, 1]])
def test_invalid_predictions(prediction):
    with pytest.raises(ValueError): metrics([1, 2], prediction)


def test_paired_blocks_reproducible_and_direction():
    days = pd.date_range("2026-10-01", periods=31).repeat(3)
    y = np.arange(93)
    first = block_bootstrap(days, y, y+2, y, repeats=50)
    assert first == block_bootstrap(days, y, y+2, y, repeats=50)
    assert first == block_bootstrap(pd.Series(days), y, y+2, y, repeats=50)
    assert first["ci95_low"] == first["ci95_high"] == -2


def test_missing_days_cannot_be_resampled_as_consecutive():
    days = pd.date_range("2026-10-01", periods=31).delete(10)
    with pytest.raises(ValueError): block_bootstrap(days, np.zeros(30), np.ones(30), np.zeros(30))
