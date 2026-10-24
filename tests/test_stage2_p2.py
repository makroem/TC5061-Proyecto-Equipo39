"""P2 de la etapa 2 con datos sintéticos: modelo de dos riesgos, umbrales y paso por el controlador."""

import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39 import config as C
from mibici_equipo39.features import FEATURE_COLUMNS
from mibici_equipo39.modeling import p2, stage2

REPO = Path(__file__).resolve().parents[1]
P2_PLAN = list(C.STAGE2_SEARCH_PLAN["p2"])
OUTPUT = ["prob_bikes", "prob_docks", "alert_bikes", "alert_docks"]


def synthetic(n=900, seed=39):
    rng = np.random.default_rng(seed)
    hour = rng.integers(0, 24, n)
    station = rng.choice(["1", "2", "3", "4", "5"], n)
    frame = pd.DataFrame({column: 0.0 for column in FEATURE_COLUMNS}, index=range(n))
    frame["hour_of_day"], frame["day_of_week"], frame["month"] = hour, rng.integers(0, 7, n), rng.integers(1, 13, n)
    frame["station_id"] = pd.array(station, dtype="string")
    peak = (hour >= 17) & (station == "1")
    frame["y_bikes"] = (peak & (rng.random(n) < 0.6)).astype(int)
    frame["y_docks"] = ((hour <= 9) & (station == "2") & (rng.random(n) < 0.6)).astype(int)
    frame["capacity"], frame["flow_min"], frame["flow_max"] = 20.0, 0, 0
    frame["split"] = np.where(np.arange(n) < 600, "train", np.where(np.arange(n) < 750, "validation", "test"))
    frame["prediction_time"] = pd.Timestamp("2026-06-01")
    return frame


@pytest.fixture
def fitted():
    data = synthetic()
    variant = {"name": "p2_lr_1", "family": "logistic", "params": dict(P2_PLAN[1]["params"])}
    return p2.ADAPTER.fit(variant, data), data


def test_risk_model_returns_four_columns_one_row_per_input(fitted):
    model, data = fitted
    out = model.model.predict(None, data[p2.COLUMNS].head(5))
    assert list(out.columns) == OUTPUT and len(out) == 5
    assert out[["prob_bikes", "prob_docks"]].stack().between(0, 1).all()
    assert out[["alert_bikes", "alert_docks"]].dtypes.eq(bool).all()


def test_forbidden_columns_are_ignored_and_missing_columns_fail(fitted):
    model, data = fitted
    rows = data.head(5)
    pd.testing.assert_frame_equal(model.model.predict(None, rows), model.model.predict(None, rows[p2.COLUMNS]))
    assert not p2.FORBIDDEN & set(p2.COLUMNS)
    with pytest.raises(ValueError, match="station_id"):
        model.model.predict(None, rows[p2.COLUMNS].drop(columns="station_id"))


def test_thresholds_come_from_the_grid_and_are_logged_as_config(fitted):
    model, _ = fitted
    config = model.extra["config"]
    assert set(config["thresholds"]) == {"bikes", "docks"}
    assert all(t in C.P2_THRESHOLDS for t in config["thresholds"].values())
    assert config["thresholds"] == model.model.thresholds
    assert config["initial_occupancy"] == C.P2_INITIAL_OCCUPANCY and "capacity" in config["excluded_columns"]
    assert len(model.extra["evaluation"]["threshold_search_validation"]["bikes"]) == len(C.P2_THRESHOLDS)


def test_metrics_have_split_prefixes_and_macro_f1(fitted):
    model, data = fitted
    metrics = p2.ADAPTER.evaluate(model, data, "validation")
    for risk in ("bikes", "docks"):
        for name in ("recall", "precision", "f1", "ap", "support_positive", "prevalence", "alerts_per_1000"):
            assert f"val_{name}_{risk}" in metrics
    assert metrics["val_macro_f1"] == pytest.approx((metrics["val_f1_bikes"] + metrics["val_f1_docks"]) / 2)


def test_single_class_train_falls_back_without_failing():
    data = synthetic()
    data.loc[data["split"].eq("train"), "y_docks"] = 0
    model = p2.ADAPTER.fit({"name": "p2_lr_1", "family": "logistic", "params": dict(P2_PLAN[1]["params"])}, data)
    out = model.model.predict(None, data[p2.COLUMNS].head(5))
    assert (out["prob_docks"] == 0).all() and not out["alert_docks"].any()


def test_controller_search_logs_a_p2_pyfunc_that_loads_in_a_new_process(stage2_env, monkeypatch):
    data = synthetic()
    monkeypatch.setattr(C, "ROOT", REPO)
    monkeypatch.setattr(C, "STAGE2_SEARCH_PLAN", {"p2": P2_PLAN})
    monkeypatch.setattr(p2.ADAPTER, "load_data", lambda: data)
    monkeypatch.setattr(stage2, "load_adapter", lambda question: p2.ADAPTER)
    parent_id = stage2_env.project_run()
    summary = stage2.main(["--question", "p2", "--member", "DiegoMartinez"])
    children = stage2_env.children(parent_id)
    assert set(children) == {"baseline", *(v["name"] for v in P2_PLAN)}
    run = children[summary["selected_variant"]]
    assert {"val_macro_f1", "test_macro_f1", "val_alerts_per_1000_bikes"} <= set(run.data.metrics)
    plots = {a.path for a in stage2_env.client.list_artifacts(run.info.run_id, "plots")}
    assert {"plots/p2_matrices_confusion_validacion.png", "plots/p2_precision_recall_validacion.png",
            "plots/p2_umbrales_validacion.png"} <= plots
    code = ("import json, sys, mlflow; from mlflow.models import Model; "
            "local = mlflow.artifacts.download_artifacts(sys.argv[1]); "
            "example = Model.load(local + '/MLmodel').load_input_example(local); "
            "print(json.dumps(list(mlflow.pyfunc.load_model(local).predict(example).columns)))")
    environment = {**os.environ, "MLFLOW_TRACKING_URI": stage2_env.uri}
    environment.pop("MLFLOW_RUN_ID", None)
    result = subprocess.run([sys.executable, "-c", code, f"runs:/{run.info.run_id}/model"], cwd=REPO,
                            env=environment, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == OUTPUT


def test_module_run_as_main_accepts_the_p2_adapter():
    environment = {k: v for k, v in os.environ.items() if k != "MLFLOW_RUN_ID"}
    result = subprocess.run([sys.executable, "-m", "mibici_equipo39.modeling.stage2", "--question", "p2",
                             "--member", "DiegoMartinez"], cwd=REPO, env=environment,
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0 and "falta MLFLOW_RUN_ID" in result.stderr, result.stderr[-2000:]
