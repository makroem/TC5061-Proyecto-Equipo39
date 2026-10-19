import numpy as np

from mibici_equipo39 import config as C
from mibici_equipo39.modeling.p2 import CATEGORICAL, FORBIDDEN, NUMERIC, choose_threshold, classification_metrics


def test_grid_is_005_to_095():
    assert C.P2_THRESHOLDS[0] == 0.05 and C.P2_THRESHOLDS[-1] == 0.95 and len(C.P2_THRESHOLDS) == 19


def test_recall_floor_picks_highest_precision_and_highest_threshold_on_tie():
    y = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    score = np.array([0.9, 0.9, 0.9, 0.9, 0.12, 0.08, 0.08, 0.02, 0.02, 0.02])
    threshold, rule = choose_threshold(y, score)
    assert rule == "recall_floor"
    assert threshold == 0.9
    assert threshold in C.P2_THRESHOLDS


def test_falls_back_to_max_f1_when_recall_is_unreachable():
    y = np.array([1, 1, 1, 1, 0, 0])
    score = np.array([0.6, 0.01, 0.01, 0.01, 0.01, 0.01])
    threshold, rule = choose_threshold(y, score)
    assert rule == "max_f1" and threshold == 0.6


def test_constant_baseline_score_ends_at_highest_threshold_with_zero_f1():
    y = np.array([1, 0, 0, 0, 0, 0, 0, 0])
    score = np.full(len(y), y.mean() / 10)
    threshold, rule = choose_threshold(y, score)
    values, _ = classification_metrics(y, score, threshold)
    assert (threshold, rule) == (0.95, "max_f1") and values["f1"] == 0.0


def test_ap_is_omitted_without_positives():
    values, _ = classification_metrics(np.zeros(5, dtype=int), np.full(5, 0.3), 0.5)
    assert values["support_positive"] == 0 and "ap" not in values


def test_x_has_no_labels_flows_or_capacity():
    assert not FORBIDDEN & set(NUMERIC + CATEGORICAL)
    assert CATEGORICAL == ["station_id"]
