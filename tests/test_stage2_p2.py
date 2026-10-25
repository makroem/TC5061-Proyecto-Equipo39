"""P2 de la etapa 2 con datos sintéticos: modelo de dos riesgos, umbrales y paso por el controlador."""

import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np
import pandas as pd
import mlflow
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


LR_1 = {"name": "p2_lr_1", "family": "logistic", "params": dict(P2_PLAN[1]["params"])}


def fit_and_calibrate(data, variant=LR_1, frozen=None):
    model = p2.ADAPTER.fit(variant, data)
    p2.ADAPTER.calibrate(model, data, frozen)
    return model


@pytest.fixture
def fitted():
    data = synthetic()
    return fit_and_calibrate(data), data


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
    model = fit_and_calibrate(data)
    out = model.model.predict(None, data[p2.COLUMNS].head(5))
    assert (out["prob_docks"] == 0).all() and not out["alert_docks"].any()


def test_fit_uses_only_train_and_leaves_thresholds_to_calibrate():
    data = synthetic()
    shuffled = data.copy()
    outside = shuffled["split"].ne("train")
    shuffled.loc[outside, ["y_bikes", "y_docks"]] = 1 - shuffled.loc[outside, ["y_bikes", "y_docks"]]
    model, other = p2.ADAPTER.fit(LR_1, data), p2.ADAPTER.fit(LR_1, shuffled)
    assert model.model.thresholds == {} and "thresholds" not in model.extra["config"]
    with pytest.raises(ValueError, match="calibrate"):
        model.model.predict(None, data[p2.COLUMNS].head(3))
    for risk in p2.TARGETS:
        np.testing.assert_allclose(p2.positive_proba(model.model.pipelines[risk], data[p2.COLUMNS]),
                                   p2.positive_proba(other.model.pipelines[risk], data[p2.COLUMNS]))


def test_calibration_uses_validation_and_never_test():
    data = synthetic()
    flipped = data.copy()
    test = flipped["split"].eq("test")
    flipped.loc[test, ["y_bikes", "y_docks"]] = 1 - flipped.loc[test, ["y_bikes", "y_docks"]]
    assert fit_and_calibrate(data).model.thresholds == fit_and_calibrate(flipped).model.thresholds
    no_val_positives = data.copy()
    no_val_positives.loc[no_val_positives["split"].eq("validation"), "y_bikes"] = 0
    assert fit_and_calibrate(no_val_positives).extra["config"]["threshold_rules"]["bikes"] == "max_f1"


def test_frozen_thresholds_are_applied_without_recomputing():
    data = synthetic()
    model = fit_and_calibrate(data, frozen={"thresholds": {"bikes": 0.95, "docks": 0.05}})
    assert model.model.thresholds == {"bikes": 0.95, "docks": 0.05}
    assert model.extra["config"]["threshold_rules"] == {"bikes": "selection", "docks": "selection"}
    assert len(model.extra["evaluation"]["threshold_search_validation"]["docks"]) == len(C.P2_THRESHOLDS)
    with pytest.raises(ValueError, match="bikes y docks"):
        fit_and_calibrate(data, frozen={"thresholds": {"bikes": 0.5}})


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


def test_reproduce_keeps_the_thresholds_frozen_in_the_selection(stage2_env, monkeypatch):
    data = synthetic()
    monkeypatch.setattr(C, "ROOT", REPO)
    monkeypatch.setattr(C, "STAGE2_SEARCH_PLAN", {"p2": P2_PLAN})
    monkeypatch.setattr(stage2, "load_adapter", lambda question: p2.ADAPTER)
    monkeypatch.setattr(p2.ADAPTER, "load_data", lambda: data)
    search_id = stage2_env.project_run()
    summary = stage2.main(["--question", "p2", "--member", "DiegoMartinez"])
    chosen = summary["selected_variant"]
    before_test = mlflow.artifacts.load_dict(f"runs:/{search_id}/evaluation/selection_before_test.json")
    frozen = before_test["calibration"][chosen]
    original = stage2_env.children(search_id)[chosen]
    assert original.data.tags["calibration_source"] == "validation"
    variant = next(v for v in [p2.ADAPTER.baseline(), *P2_PLAN] if v["name"] == chosen)
    selection = stage2_env.path / "etapa2/selection.json"
    selection.write_text(json.dumps({"p2": {**variant, "variant": chosen, "run_id": original.info.run_id}}))
    stage2_env.project_run()
    with pytest.raises(ValueError, match="calibración congelada"):
        stage2.main(["--question", "p2", "--model", "selected", "--mode", "reproduce", "--member", "Marco"])

    selection.write_text(json.dumps({"p2": {**variant, "variant": chosen, "run_id": original.info.run_id,
                                            "calibration": frozen}}))
    val = data["split"].eq("validation")
    data.loc[val, ["y_bikes", "y_docks"]] = 1 - data.loc[val, ["y_bikes", "y_docks"]]
    recomputed = fit_and_calibrate(data, variant).model.thresholds
    assert recomputed != frozen["thresholds"]
    parent_id = stage2_env.project_run()
    stage2.main(["--question", "p2", "--model", "selected", "--mode", "reproduce", "--member", "Marco"])
    child = stage2_env.children(parent_id)[chosen]
    resolved = mlflow.artifacts.load_dict(f"runs:/{child.info.run_id}/config/resolved.json")
    assert resolved["thresholds"] == frozen["thresholds"] and child.data.tags["calibration_source"] == "selection"
