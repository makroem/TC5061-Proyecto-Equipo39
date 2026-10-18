import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.features import (
    add_calendar_features,
    add_lagged_features,
    aggregate_hourly,
    make_events,
    random_grouped_split,
)

STATIONS = pd.DataFrame({"station_id": pd.array(["1", "2"], dtype="string")})


def views(rows):
    df = pd.DataFrame(rows, columns=["station_id", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def grid(n=200, seed=39):
    rng = np.random.default_rng(seed)
    hours = pd.date_range("2026-01-01", periods=n, freq="h")
    return pd.DataFrame({
        "station_id": pd.array(["1"] * n + ["2"] * n, dtype="string"),
        "hour": list(hours) * 2,
        "departures": rng.integers(0, 9, 2 * n),
        "arrivals": rng.integers(0, 9, 2 * n),
    })


def test_hours_are_left_closed_and_quiet_hours_are_zero():
    dep = views([("1", "2026-01-01 10:59:59"), ("1", "2026-01-01 11:00:00"), ("9", "2026-01-01 10:10:00")])
    arr = views([("2", "2026-01-01 12:30:00")])
    hourly = aggregate_hourly(make_events(dep, arr), STATIONS, "2026-01-01 10:00", "2026-01-01 13:00")
    assert hourly.loc[hourly.station_id.eq("1"), "departures"].tolist() == [1, 1, 0]
    assert hourly.loc[hourly.station_id.eq("2"), "arrivals"].tolist() == [0, 0, 1]
    assert set(hourly.station_id) == {"1", "2"}


def test_future_events_do_not_change_features_at_t():
    base = add_lagged_features(add_calendar_features(grid()))
    changed = grid()
    t = 180
    changed.loc[t:, "departures"] += 50
    again = add_lagged_features(add_calendar_features(changed))
    cols = ["dep_lag_1", "dep_lag_168", "dep_mean_24", "dep_mean_168", "net_sum_24"]
    assert np.allclose(base.loc[t, cols].astype(float), again.loc[t, cols].astype(float))
    assert base.dep_lag_1[t] == base.departures[t - 1]
    assert base.dep_lag_168[t] == base.departures[t - 168]


def test_one_station_does_not_change_another():
    base = add_lagged_features(grid())
    changed = grid()
    changed.loc[changed.station_id.eq("1"), "departures"] += 10
    again = add_lagged_features(changed)
    other = base.station_id.eq("2")
    assert base.loc[other, "dep_mean_24"].equals(again.loc[other, "dep_mean_24"])


def test_incomplete_grid_fails():
    with pytest.raises(ValueError):
        add_lagged_features(grid().drop(index=[5]))


def test_split_keeps_whole_days_is_repeatable_and_balanced():
    hours = pd.DataFrame({"hour": pd.date_range("2025-10-09", "2026-09-30 23:00", freq="h")})
    first, manifest = random_grouped_split(hours)
    second, again = random_grouped_split(hours)
    assert manifest["split_id"] == again["split_id"] and first["split"].equals(second["split"])
    assert first.groupby(first.hour.dt.date)["split"].nunique().eq(1).all()
    share = pd.Series({k: len(v) for k, v in manifest["days"].items()}) / first.hour.dt.date.nunique()
    assert (share - pd.Series({"train": 0.70, "validation": 0.15, "test": 0.15})).abs().max() < 0.01
    months = first.groupby([first.hour.dt.to_period("M"), "split"]).size().unstack()
    assert (months > 0).all().all()
