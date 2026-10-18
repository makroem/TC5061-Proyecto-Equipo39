import pandas as pd

from mibici_equipo39.features import intra_hour_extremes, make_capacity_proxy_targets, make_events, proxy_labels

HOUR = pd.Timestamp("2026-03-02 08:00")


def events(signs, seconds=None, station="1"):
    seconds = list(seconds if seconds is not None else range(len(signs)))
    times = HOUR + pd.to_timedelta(seconds, unit="s")
    dep = pd.DataFrame({"station_id": station, "timestamp": [t for t, s in zip(times, signs) if s < 0]})
    arr = pd.DataFrame({"station_id": station, "timestamp": [t for t, s in zip(times, signs) if s > 0]})
    return make_events(dep, arr)


def extremes(df):
    row = intra_hour_extremes(df).iloc[0]
    return int(row.flow_min), int(row.flow_max)


def labels(flow_min, flow_max, capacity):
    return proxy_labels(pd.Series([flow_min]), pd.Series([flow_max]), pd.Series([float(capacity)]))


def test_capacity_changes_the_label():
    low, _ = extremes(events([-1] * 8))
    assert low == -8
    assert labels(low, 0, 20)[0][0] == 1
    assert labels(low, 0, 40)[0][0] == 0
    assert labels(0, 8, 20)[1][0] == 1


def test_transient_pressure_counts_even_if_final_flow_is_zero():
    low, high = extremes(events([-1] * 8 + [1] * 8))
    assert (low, high) == (-8, 0)
    assert labels(low, high, 20)[0][0] == 1


def test_simultaneous_events_are_netted_first():
    assert extremes(events([-1, 1, -1, 1], seconds=[5, 5, 9, 9])) == (0, 0)


def test_invalid_capacity_is_excluded_and_quiet_hours_are_zero():
    hourly = pd.DataFrame({
        "station_id": pd.array(["1", "1", "2"], dtype="string"),
        "hour": [HOUR, HOUR + pd.Timedelta("1h"), HOUR],
    })
    stations = pd.DataFrame({
        "station_id": pd.array(["1", "2"], dtype="string"),
        "capacity": pd.array([20, 0], dtype="Int64"),
        "valid_capacity": pd.array([True, False], dtype="boolean"),
    })
    targets = make_capacity_proxy_targets(hourly, events([-1] * 8), stations)
    assert targets["y_bikes"].tolist()[:2] == [1, 0]
    assert targets["y_bikes"].isna().tolist() == [False, False, True]
    assert targets["flow_min"].tolist() == [-8, 0, 0]
