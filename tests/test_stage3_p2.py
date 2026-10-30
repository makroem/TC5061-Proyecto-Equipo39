"""Límites y errores de P2 para la etapa 3; datos sintéticos, sin almacén de MLflow."""

import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyClassifier

from mibici_equipo39 import config as C
from mibici_equipo39.features import FEATURE_COLUMNS, proxy_labels
from mibici_equipo39.modeling import p2, stage2


class FixedProbability:
    """Pipeline mínimo que devuelve una probabilidad conocida para probar el umbral."""

    classes_ = np.array([0, 1])

    def __init__(self, values):
        self.values = np.asarray(values, dtype=float)

    def predict_proba(self, X):
        return np.column_stack([1 - self.values, self.values])


def model_input(n=3):
    rng = np.random.default_rng(39)
    X = pd.DataFrame({c: rng.uniform(0, 1, n) for c in FEATURE_COLUMNS})
    X["station_id"] = [str(i % 2) for i in range(n)]
    return X


def test_proxy_labels_are_inclusive_at_the_margin():
    # Capacidad 10 y ocupación 50%: inventario inicial 5, margen de 1 y de 9 anclajes.
    capacity = pd.Series([10.0] * 4)
    y_bikes, y_docks = proxy_labels(pd.Series([-4, -3, 0, 0]), pd.Series([0, 0, 4, 3]), capacity)

    assert y_bikes.tolist() == [1, 0, 0, 0]
    assert y_docks.tolist() == [0, 0, 1, 0]


def test_alert_fires_when_the_probability_equals_the_threshold():
    model = p2.P2RiskModel({"bikes": FixedProbability([0.65, 0.6499, 0.9]),
                            "docks": FixedProbability([0.70, 0.1, 0.71])},
                           {"bikes": 0.65, "docks": 0.70})

    out = model.predict(None, model_input())

    assert out["alert_bikes"].tolist() == [True, False, True]
    assert out["alert_docks"].tolist() == [True, False, True]


def test_empty_input_returns_the_four_columns_without_rows():
    rng = np.random.default_rng(7)
    X = model_input(50)
    pipelines = {risk: p2.make_candidate().fit(X[p2.COLUMNS], rng.integers(0, 2, 50))
                 for risk in p2.TARGETS}

    out = p2.P2RiskModel(pipelines, {"bikes": 0.5, "docks": 0.5}).predict(None, X.iloc[:0])

    assert list(out.columns) == ["prob_bikes", "prob_docks", "alert_bikes", "alert_docks"]
    assert out.empty


def test_a_train_with_only_positives_gives_probability_one():
    X = model_input(4)
    only_positive = DummyClassifier(strategy="prior").fit(X[p2.COLUMNS], [1, 1, 1, 1])
    only_negative = DummyClassifier(strategy="prior").fit(X[p2.COLUMNS], [0, 0, 0, 0])

    assert p2.positive_proba(only_positive, X[p2.COLUMNS]).tolist() == [1.0] * 4
    assert p2.positive_proba(only_negative, X[p2.COLUMNS]).tolist() == [0.0] * 4


def test_validation_without_positives_falls_back_to_the_highest_threshold():
    threshold, rule = p2.choose_threshold(np.zeros(20, dtype=int), np.linspace(0, 1, 20))

    assert (threshold, rule) == (max(C.P2_THRESHOLDS), "max_f1")


def test_probabilities_stay_in_the_unit_interval_and_alerts_follow_thresholds():
    rng = np.random.default_rng(7)
    X = model_input(400)
    pipelines = {risk: p2.make_candidate().fit(X[p2.COLUMNS], rng.integers(0, 2, 400))
                 for risk in p2.TARGETS}
    thresholds = {"bikes": 0.4, "docks": 0.6}

    out = p2.P2RiskModel(pipelines, thresholds).predict(None, X)

    for risk, threshold in thresholds.items():
        assert out[f"prob_{risk}"].between(0, 1).all()
        assert out[f"alert_{risk}"].equals(out[f"prob_{risk}"] >= threshold)


def test_non_numeric_calendar_values_are_rejected():
    rng = np.random.default_rng(7)
    X = model_input(50)
    pipelines = {risk: p2.make_candidate().fit(X[p2.COLUMNS], rng.integers(0, 2, 50))
                 for risk in p2.TARGETS}
    bad = X.astype({"hour_of_day": object})
    bad.loc[0, "hour_of_day"] = "ocho"

    with pytest.raises(ValueError):
        p2.P2RiskModel(pipelines, {"bikes": 0.5, "docks": 0.5}).predict(None, bad)


def test_reproduce_refuses_a_selection_without_frozen_thresholds(monkeypatch):
    monkeypatch.setattr(stage2, "read_selection", lambda question: {
        "variant": "p2_lr_0.1", "run_id": "seleccionada", "calibration": {}})

    with pytest.raises(ValueError, match="calibración congelada"):
        stage2.run_reproduce(p2.P2Adapter(), None, {"variants": [{"name": "p2_lr_0.1"}]}, {}, "0")
