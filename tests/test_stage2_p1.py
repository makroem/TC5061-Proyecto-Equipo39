
"""
P1 de la etapa 1 con datos sintéticos
Incluye prueba de search logs, serializacion,
"""

import pickle
import pytest
import mlflow

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

import json
import os
import subprocess
import sys
from pathlib import Path

from mibici_equipo39 import config as C
from mibici_equipo39.features import FEATURE_COLUMNS
from mibici_equipo39.modeling.p1 import (
    SeasonalMeanBaseline,
    StationEncodedRegressor,
)

from mibici_equipo39.modeling import p1, stage2

REPO = Path(__file__).resolve().parents[1]
P1_PLAN = list(C.STAGE2_SEARCH_PLAN["p1"])

def synthetic_p1():
    n = 300

    frame = pd.DataFrame(
        {
            "station_id": ["A"] * n,
            "day_of_week": np.arange(n) % 7,
            "hour_of_day": np.arange(n) % 24,
            "month": 1,
            "is_weekend": 0,
            "hour_sin": 0.0,
            "hour_cos": 1.0,
            "month_sin": 0.5,
            "month_cos": 0.5,
            "split": np.where(
                np.arange(n) < 200,
                "train",
                np.where(np.arange(n) < 250, "validation", "test"),
            ),
            "prediction_time": pd.Timestamp("2026-06-01"),
        }
    )
    
    X = frame[FEATURE_COLUMNS].copy()
    y = pd.Series(np.random.default_rng(39).integers(0, 20, size=n))
    
    return {"metadata": frame[
        [
            "station_id",
            "split", 
            "prediction_time",
            ]
        ].copy(),
        "X": X,
        "y": y,
        }

def test_controller_search_logs_a_p1_model_that_loads_in_a_new_process(
    stage2_env,
    monkeypatch,):
    
    data = synthetic_p1()
    monkeypatch.setattr(C, "ROOT", REPO)
    monkeypatch.setattr(p1.ADAPTER, "load_data", lambda: data)
    monkeypatch.setattr(
        stage2,
        "load_adapter", 
        lambda question: p1.ADAPTER,)
    monkeypatch.setattr(C, "STAGE2_SEARCH_PLAN", {"p1": P1_PLAN})
    
    parent_id = stage2_env.project_run()
    summary = stage2.main(
        [
            "--question",
            "p1",
            "--member",
            "Stefania",
        ]
    )

    run = stage2_env.children(parent_id)[summary["selected_variant"]]
    expected = mlflow.artifacts.load_dict(
    f"runs:/{run.info.run_id}/evaluation/example_prediction.json")

    code = ("import json, sys, mlflow; "
            "from pathlib import Path;"
            "from mlflow.models import Model;"
           "local = mlflow.artifacts.download_artifacts(sys.argv[1]); "
           "example=Model.load(str(Path(local) / 'MLmodel')).load_input_example(local);"
           "pred=mlflow.pyfunc.load_model(local).predict(example);"
           "print(json.dumps(pred.tolist()))"
    )
    environment = {**os.environ, "MLFLOW_TRACKING_URI": stage2_env.uri}
    environment.pop("MLFLOW_RUN_ID", None)
    result = subprocess.run([sys.executable, "-c", code, f"runs:/{run.info.run_id}/model"], cwd=REPO,
                           env=environment, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr[-2000:]
    got = json.loads(
        result.stdout.strip().splitlines()[-1]
        )
    np.testing.assert_allclose(got, expected["data"],)

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

def test_pickle_serialization_preserves_predictions():
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
    unseen["station_id"] = "station_not_seen"

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
    
    
def test_missing_station_id_column_raises_error():
    frame = sample_frame().drop(columns=["station_id"])
    y = sample_target()

    model = StationEncodedRegressor(
        HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS)
    )

    with pytest.raises(KeyError, match="station_id"):
        model.fit(frame, y)