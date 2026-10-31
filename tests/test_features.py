import pandas as pd
import numpy as np

from mibici_equipo39.features import aggregate_hourly, make_events, chronological_split, add_calendar_features

STATIONS = pd.DataFrame({"station_id": pd.array(["1", "2"], dtype="string")})


def views(rows):
    df = pd.DataFrame(rows, columns=["station_id", "timestamp"])
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def test_hours_are_left_closed_and_quiet_hours_are_zero():
    dep = views([("1", "2026-01-01 10:59:59"), ("1", "2026-01-01 11:00:00"), ("9", "2026-01-01 10:10:00")])
    arr = views([("2", "2026-01-01 12:30:00")])
    hourly = aggregate_hourly(make_events(dep, arr), STATIONS, "2026-01-01 10:00", "2026-01-01 13:00")
    assert hourly.loc[hourly.station_id.eq("1"), "departures"].tolist() == [1, 1, 0]
    assert hourly.loc[hourly.station_id.eq("2"), "arrivals"].tolist() == [0, 0, 1]
    assert set(hourly.station_id) == {"1", "2"}


def test_split_keeps_whole_days_is_repeatable_and_chronological():
    hours = pd.DataFrame({"hour": pd.date_range("2025-10-01", "2026-09-30 23:00", freq="h")})
    first, manifest = chronological_split(hours)
    second, again = chronological_split(hours)
    assert manifest["split_id"] == again["split_id"] and first["split"].equals(second["split"])
    assert first.groupby(first.hour.dt.date)["split"].nunique().eq(1).all()
    assert {k:len(v) for k,v in manifest['days'].items()} == {'train':243,'validation':61,'test':61}
    assert first.loc[first.split.eq('train'),'hour'].max() < first.loc[first.split.eq('validation'),'hour'].min()
    assert first.loc[first.split.eq('validation'),'hour'].max() < first.loc[first.split.eq('test'),'hour'].min()

def test_weekend_flag_matches_calendar():
    frame = pd.DataFrame({
        "hour": pd.to_datetime([
            "2026-01-02 12:00:00",  # viernes
            "2026-01-03 12:00:00",  # sábado
            "2026-01-04 12:00:00",  # domingo
            "2026-01-05 12:00:00",  # lunes
        ])
    })

    result = add_calendar_features(frame)

    assert result["is_weekend"].tolist() == [0, 1, 1, 0]
    
def test_cyclic_features_match_expected_hour_and_month_values():
    frame = pd.DataFrame({
        "hour": pd.to_datetime([
            "2026-01-01 00:00:00",
            "2026-04-01 06:00:00",
        ])
    })

    result = add_calendar_features(frame)

    # Hora 0
    assert np.isclose(result.loc[0, "hour_sin"], 0.0)
    assert np.isclose(result.loc[0, "hour_cos"], 1.0)

    # Hora 6
    assert np.isclose(result.loc[1, "hour_sin"], 1.0)
    assert np.isclose(result.loc[1, "hour_cos"], 0.0)

    # Mes 1
    assert np.isclose(result.loc[0, "month_sin"], 0.5)
    assert np.isclose(result.loc[0, "month_cos"], np.sqrt(3) / 2)

    # Mes 4
    assert np.isclose(result.loc[1, "month_sin"], np.sqrt(3) / 2)
    assert np.isclose(result.loc[1, "month_cos"], -0.5)