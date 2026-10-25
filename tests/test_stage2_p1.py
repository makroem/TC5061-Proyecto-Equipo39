# -*- coding: utf-8 -*-
"""
Created on Sat Oct 24 09:36:43 2026

@author: stefa
"""

import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from mibici_equipo39 import config as C
from mibici_equipo39.modeling.p1 import (
    SeasonalMeanBaseline,
    StationEncodedRegressor,
)

def sample_frame():
    return pd.DataFrame(
        {
            "station_id": ["A", "A", "B", "B", "C", "C"],
            "day_of_week": [1, 2, 3, 4, 5, 6],
            "hour_of_day": [8, 9, 10, 11, 12, 13],
            "month": [1, 1, 1, 1, 1, 1],
            "is_weekend": [0, 0, 0, 0, 1, 1],
            "hour_sin": [0.0] * 6,
            "hour_cos": [1.0] * 6,
            "month_sin": [0.5] * 6,
            "month_cos": [0.5] * 6,
        }
    )

def sample_target():
    return pd.Series([10, 12, 8, 15, 7, 11])

def test_serialization_preserves_predictions():
    frame = sample_frame()
    y = sample_target()

    model = StationEncodedRegressor(
        HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS)
    )

    model.fit(frame, y)

    original = model.predict(frame)

    restored = pickle.loads(
        pickle.dumps(model)
    )

    recovered = restored.predict(frame)

    assert np.allclose(original, recovered)
    
def test_unseen_station_does_not_fail():
    frame = sample_frame()
    y = sample_target()

    model = StationEncodedRegressor(
        HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS)
    )

    model.fit(frame, y)

    unseen = frame.copy()
    unseen["station_id"] == "station_not_seen"

    pred = model.predict(unseen)

    assert len(pred) == len(unseen)
    
def test_predictions_are_non_negative():
    frame = sample_frame()
    y = sample_target()

    model = StationEncodedRegressor(
        HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS)
    )

    model.fit(frame, y)

    pred = model.predict(frame)

    assert np.all(pred >= 0)
    
def test_predict_returns_one_value_per_row():
    frame = sample_frame()
    y = sample_target()

    model = StationEncodedRegressor(
        HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS)
    )

    model.fit(frame, y)

    pred = model.predict(frame)

    assert len(pred) == len(frame)
    
def test_baseline_fallback_returns_value():
    frame = sample_frame()
    y = sample_target()

    baseline = SeasonalMeanBaseline().fit(frame, y)

    unseen = pd.DataFrame(
        {
            "station_id": ["station_not_seen"],
            "day_of_week": [6],
            "hour_of_day": [23],
        }
    )

    pred = baseline.predict(unseen)

    assert not np.isnan(pred).any()
    assert pred[0] >= 0