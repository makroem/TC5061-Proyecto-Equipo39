"""Etapa 3: casos de borde y contratos negativos de P3.

Los datos son completamente sinteticos; no se accede a CSV reales,
MLflow, Model Registry ni los manifiestos oficiales.
"""

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39.features import station_usage_profiles
from mibici_equipo39.modeling.p3 import (
    ADAPTER,
    build_p3_artifacts,
    cluster_metrics,
    fit_p3_variant,
    p3_model_cost_metrics,
    p3_stability_scores,
)


def _hours_by_day_type():
    # Lunes y sabado: salidas intencionalmente distintas por tipo de dia.
    return pd.DataFrame(
        {
            "station_id": ["A"] * 4,
            "prediction_time": pd.to_datetime(
                [
                    "2026-01-05 08:00",
                    "2026-01-05 09:00",
                    "2026-01-10 08:00",
                    "2026-01-10 09:00",
                ]
            ),
            "departures": [2, 6, 3, 1],
        }
    )


def _empty_train_frame():
    return pd.DataFrame(
        {
            "station_id": pd.Series(dtype="str"),
            "prediction_time": pd.Series(dtype="datetime64[ns]"),
            "departures": pd.Series(dtype="float64"),
        }
    )


def test_p3_profile_separates_weekday_weekend_and_normalizes():
    profile = station_usage_profiles(_hours_by_day_type(), ["A"])

    assert profile.shape == (1, 48)
    assert profile.loc["A", "weekday_hour_08"] == pytest.approx(0.25)
    assert profile.loc["A", "weekday_hour_09"] == pytest.approx(0.75)
    assert profile.loc["A", "weekend_hour_08"] == pytest.approx(0.75)
    assert profile.loc["A", "weekend_hour_09"] == pytest.approx(0.25)
    assert profile.loc["A", "weekday_hour_18"] == 0
    assert profile.loc["A", "weekend_hour_18"] == 0
    assert profile.filter(like="weekday_").sum(axis=1).iloc[0] == pytest.approx(1)
    assert profile.filter(like="weekend_").sum(axis=1).iloc[0] == pytest.approx(1)


def test_p3_missing_station_has_finite_zero_profile():
    profile = station_usage_profiles(_hours_by_day_type(), ["A", "MISSING"])

    assert list(profile.index) == ["A", "MISSING"]
    assert profile.shape == (2, 48)
    assert np.isfinite(profile.to_numpy()).all()
    assert (profile.loc["MISSING"] == 0).all()


def test_p3_zero_weights_never_create_nan_or_infinite_profiles():
    frame = _hours_by_day_type()
    frame["sample_weight"] = 0.0

    profile = station_usage_profiles(frame, ["A"], weight="sample_weight")

    assert np.isfinite(profile.to_numpy()).all()
    assert (profile.loc["A"] == 0).all()


def test_p3_negative_bootstrap_weights_are_rejected():
    frame = _hours_by_day_type()
    frame["sample_weight"] = [1.0, 1.0, -1.0, 1.0]

    with pytest.raises(ValueError, match="negativos"):
        station_usage_profiles(frame, ["A"], weight="sample_weight")


def test_p3_stability_requires_complete_train_schema():
    frame = _empty_train_frame().drop(columns=["departures"])

    with pytest.raises(ValueError, match="faltan columnas"):
        p3_stability_scores(
            frame,
            ["A"],
            pd.DataFrame(np.zeros((1, 48))),
            [0],
            "kmeans",
            {"n_clusters": 2},
            n_bootstraps=1,
        )


def test_p3_stability_rejects_empty_training_days():
    with pytest.raises(ValueError, match="no hay dias|no hay días"):
        p3_stability_scores(
            _empty_train_frame(),
            ["A", "B"],
            pd.DataFrame(np.zeros((2, 48))),
            [0, 1],
            "kmeans",
            {"n_clusters": 2},
            n_bootstraps=1,
        )


def test_p3_stability_rejects_wrong_number_of_reference_labels():
    with pytest.raises(ValueError, match="una asignación por estación"):
        p3_stability_scores(
            _hours_by_day_type(),
            ["A", "B"],
            pd.DataFrame(np.zeros((2, 48))),
            [0],
            "kmeans",
            {"n_clusters": 2},
            n_bootstraps=1,
        )


def test_p3_cost_rejects_invalid_repeat_count_before_prediction():
    with pytest.raises(ValueError, match="repeats"):
        p3_model_cost_metrics(
            object(),
            pd.DataFrame(np.zeros((4, 48))),
            fit_seconds=0.1,
            repeats=0,
        )


def test_p3_cluster_metrics_omit_undefined_scores_for_singletons():
    # Un cluster por observacion: silhouette y Davies-Bouldin no son definibles.
    X = np.arange(5 * 48, dtype=float).reshape(5, 48)
    labels = np.arange(5)

    metrics = cluster_metrics(X, labels, "val")

    assert metrics["val_n_clusters"] == 5
    assert metrics["val_min_cluster_size"] == 1
    assert "val_silhouette" not in metrics
    assert "val_davies_bouldin" not in metrics


def test_p3_artifacts_reject_missing_catalog_coordinates(tmp_path):
    profiles = pd.DataFrame(np.ones((3, 48)))
    stations = pd.DataFrame(
        {
            "station_id": ["A", "B", "C"],
            "station_name": ["A", "B", "C"],
            "latitude": [20.6, 20.7, 20.8],
        }
    )
    with pytest.raises(ValueError, match="faltan columnas"):
        build_p3_artifacts(
            profiles,
            ["A", "B", "C"],
            np.array([0, 1, 2]),
            stations,
            tmp_path,
        )


def test_p3_fit_requires_training_and_validation_periods():
    with pytest.raises(ValueError, match="faltan perfiles"):
        fit_p3_variant(
            {"validation": pd.DataFrame(np.ones((4, 48)))},
            "kmeans",
            {"n_clusters": 2},
            seed=39,
        )


def test_p3_adapter_rejects_unknown_split_before_accessing_model():
    with pytest.raises(ValueError, match="split desconocido"):
        ADAPTER.evaluate(object(), {}, "invalid_split")
