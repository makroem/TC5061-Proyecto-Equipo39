"""Regresiones contra uniones incorrectas y comparaciones de temporadas incompatibles."""

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.monitoring.common import load_config
from mibici_equipo39.monitoring.prepare import calendar_frame
from mibici_equipo39.monitoring.seasonal import attach_predictions, describe, seasonal_pair, standardized_comparison


def grid(year):
    keys = pd.MultiIndex.from_product([["10","20"],pd.date_range(f"{year}-10-01",f"{year}-11-01",freq="h",inclusive="left")],names=["station_id","prediction_time"])
    frame = calendar_frame(keys.to_frame(index=False))
    frame["target_departures"] = 2
    frame["prediction_a"] = 1.0
    return frame


def test_predictions_join_by_keys_not_row_position():
    frame = grid(2026).drop(columns="prediction_a")
    pred = frame[["station_id","prediction_time","target_departures"]].copy()
    pred["prediction_a"] = np.arange(len(pred),dtype=float)
    merged = attach_predictions(frame,pred.sample(frac=1,random_state=9))
    np.testing.assert_array_equal(merged.prediction_a, np.arange(len(pred)))


@pytest.mark.parametrize("fault",["duplicate","missing","wrong_target","negative","infinite","shifted_key"])
def test_prediction_alignment_rejects_corruption(fault):
    pred = grid(2026)
    frame = pred.drop(columns="prediction_a")
    pred = pred[["station_id","prediction_time","target_departures","prediction_a"]].copy()
    if fault=="duplicate": pred.iloc[1] = pred.iloc[0]
    if fault=="missing": pred = pred.iloc[:-1]
    if fault=="wrong_target": pred.loc[0,"target_departures"] = 7
    if fault=="negative": pred.loc[0,"prediction_a"] = -1
    if fault=="infinite": pred.loc[0,"prediction_a"] = np.inf
    if fault=="shifted_key": pred.loc[0,"prediction_time"] += pd.Timedelta(days=365)
    with pytest.raises(ValueError): attach_predictions(frame,pred)


def test_same_month_same_stations_and_complete_grid():
    reference, current = grid(2025), grid(2026)
    reference = reference[reference.station_id.eq("10")]
    a,b,summary = seasonal_pair(reference,current,load_config())
    assert len(a)==len(b)==744
    assert summary["stations"]==1
    assert set(a.station_id)==set(b.station_id)=={"10"}
    assert a.month.eq(10).all() and b.month.eq(10).all()


@pytest.mark.parametrize("fault",["other_season","missing_hour"])
def test_incomplete_season_is_not_silently_substituted(fault):
    ref = grid(2025)
    if fault=="other_season": ref.prediction_time += pd.DateOffset(months=1)
    else: ref = ref.iloc[1:]
    with pytest.raises(ValueError): seasonal_pair(ref,grid(2026),load_config())


def test_standardization_removes_calendar_mix_without_hiding_growth():
    a,b = grid(2025),grid(2026)
    for frame in (a,b):
        frame["target_departures"] = frame.day_of_week+1
        frame["prediction_a"] = frame.day_of_week+1.0
    b["target_departures"] *= 2
    result = standardized_comparison(a,b)
    assert result["target_departures"]["change_pct"] == pytest.approx(100)
    assert result["prediction_a"]["change_pct"] == pytest.approx(0)


def test_bias_direction_and_shortfall_are_explicit():
    result = describe(grid(2026))
    assert result["bias_prediction_minus_observed"] == -1
    assert result["aggregate_underestimate_pct"] == 50
    assert result["mae"] == result["rmse"] == 1


def test_evidently_includes_target_prediction_and_nine_feature_denominator(tmp_path):
    from mibici_equipo39.monitoring.seasonal import make_report
    a,b = grid(2025),grid(2026)
    a["target_departures"] = a.hour_of_day
    b["target_departures"] = b.hour_of_day+20
    a["prediction_a"] = a.hour_of_day+0.5
    b["prediction_a"] = b.hour_of_day+0.5
    c = {**load_config(), "drift_sample_size":1000}
    report = make_report(a,b,c,"prueba",tmp_path)
    values = {v["variable"]:v for v in report["variables"]}
    assert set(values)==set(c["features"]+["target_departures","prediction_a"])
    assert values["target_departures"]["drift"]
    assert not values["prediction_a"]["drift"]
    assert report["features_total"]==9
    assert (tmp_path/"drift_prueba.html").is_file()
