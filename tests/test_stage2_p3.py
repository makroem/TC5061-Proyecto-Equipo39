import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline


from mibici_equipo39.features import station_usage_profiles
from mibici_equipo39.modeling.p3 import (
    build_p3_pipeline,
    cluster_metrics,
    fit_p3_variant,
    p3_stability_scores,
)


def synthetic_profiles(n_samples=24, n_features=48):
    """Perfiles sintéticos con la misma dimensión utilizada por P3."""
    rng = np.random.default_rng(39)
    return pd.DataFrame(
        rng.normal(size=(n_samples, n_features)),
        columns=[f"profile_{i:02d}" for i in range(n_features)],
    )


@pytest.mark.parametrize(
    ("family", "params", "expected_type", "expected_groups"),
    [
        (
            "kmeans",
            {"n_clusters": 3, "n_init": 20, "max_iter": 300},
            KMeans,
            3,
        ),
        (
            "kmeans",
            {"n_clusters": 4, "n_init": 20, "max_iter": 300},
            KMeans,
            4,
        ),
        (
            "kmeans",
            {"n_clusters": 5, "n_init": 20, "max_iter": 300},
            KMeans,
            5,
        ),
        (
            "gmm",
            {
                "n_components": 3,
                "covariance_type": "diag",
                "n_init": 5,
                "max_iter": 300,
                "reg_covar": 1e-6,
            },
            GaussianMixture,
            3,
        ),
    ],
)
def test_build_p3_pipeline_supports_stage2_variants(
    family, params, expected_type, expected_groups
):
    pipeline = build_p3_pipeline(family, params, seed=39)

    assert isinstance(pipeline, Pipeline)
    assert list(pipeline.named_steps) == ["scaler", "model"]
    assert isinstance(pipeline.named_steps["model"], expected_type)

    if family == "kmeans":
        assert pipeline.named_steps["model"].n_clusters == expected_groups
    else:
        assert pipeline.named_steps["model"].n_components == expected_groups


def test_p3_pipeline_uses_48_profile_features():
    X = synthetic_profiles()

    pipeline = build_p3_pipeline(
        "kmeans",
        {"n_clusters": 3, "n_init": 20, "max_iter": 300},
        seed=39,
    )
    pipeline.fit(X)

    assert pipeline.named_steps["scaler"].n_features_in_ == 48
    predictions = pipeline.predict(X)

    assert predictions.shape == (len(X),)


def test_predict_does_not_refit_scaler_on_future_profiles():
    train = synthetic_profiles()
    future = synthetic_profiles() + 100.0

    pipeline = build_p3_pipeline(
        "kmeans",
        {"n_clusters": 3, "n_init": 20, "max_iter": 300},
        seed=39,
    )
    pipeline.fit(train)

    mean_before = pipeline.named_steps["scaler"].mean_.copy()

    predictions = pipeline.predict(future)

    np.testing.assert_allclose(
        pipeline.named_steps["scaler"].mean_,
        mean_before,
    )
    assert predictions.shape == (len(future),)


def test_unknown_p3_family_is_rejected():
    with pytest.raises(ValueError, match="familia"):
        build_p3_pipeline("modelo_desconocido", {}, seed=39)


def test_cluster_metrics_do_not_invent_silhouette_for_one_group():
    X = np.zeros((8, 48))
    labels = np.zeros(8, dtype=int)

    metrics = cluster_metrics(X, labels, "val")

    assert metrics["val_n_clusters"] == 1
    assert "val_silhouette" not in metrics
    assert "val_davies_bouldin" not in metrics

def test_fit_p3_variant_returns_pipeline_labels_and_metrics():
    profiles = {
        "train": synthetic_profiles(),
        "validation": synthetic_profiles() + 0.25,
        "test": synthetic_profiles() + 0.50,
    }

    result = fit_p3_variant(
        profiles,
        "kmeans",
        {"n_clusters": 3, "n_init": 20, "max_iter": 300},
        seed=39,
    )

    assert isinstance(result["pipeline"], Pipeline)

    assert set(result["labels"]) == {
        "train",
        "validation",
        "test",
    }

    assert len(result["labels"]["train"]) == len(profiles["train"])
    assert len(result["labels"]["validation"]) == len(
        profiles["validation"]
    )
    assert len(result["labels"]["test"]) == len(profiles["test"])

    assert "train_n_clusters" in result["metrics"]
    assert "val_n_clusters" in result["metrics"]
    assert "test_n_clusters" in result["metrics"]


def test_future_profiles_do_not_change_train_fit():
    train = synthetic_profiles()

    profiles_a = {
        "train": train.copy(),
        "validation": synthetic_profiles() + 10.0,
        "test": synthetic_profiles() + 20.0,
    }

    profiles_b = {
        "train": train.copy(),
        "validation": synthetic_profiles() + 1000.0,
        "test": synthetic_profiles() - 1000.0,
    }

    result_a = fit_p3_variant(
        profiles_a,
        "kmeans",
        {"n_clusters": 3, "n_init": 20, "max_iter": 300},
        seed=39,
    )

    result_b = fit_p3_variant(
        profiles_b,
        "kmeans",
        {"n_clusters": 3, "n_init": 20, "max_iter": 300},
        seed=39,
    )

    np.testing.assert_allclose(
        result_a["pipeline"].named_steps["scaler"].mean_,
        result_b["pipeline"].named_steps["scaler"].mean_,
    )

    np.testing.assert_array_equal(
        result_a["labels"]["train"],
        result_b["labels"]["train"],
    )


def test_fit_p3_variant_rejects_missing_period():
    profiles = {
        "train": synthetic_profiles(),
        "validation": synthetic_profiles(),
    }

    with pytest.raises(ValueError, match="faltan perfiles"):
        fit_p3_variant(
            profiles,
            "kmeans",
            {"n_clusters": 3, "n_init": 20, "max_iter": 300},
            seed=39,
        )

def synthetic_daily_usage(n_stations=12, n_days=28):
    """Genera días completos para probar estabilidad temporal de P3."""
    rng = np.random.default_rng(39)
    start = pd.Timestamp("2026-01-01")
    rows = []

    for day in range(n_days):
        for station in range(n_stations):
            group = station % 3

            for hour in range(24):
                if group == 0:
                    peak = 4.0 if 7 <= hour <= 10 else 1.0
                elif group == 1:
                    peak = 4.0 if 16 <= hour <= 19 else 1.0
                else:
                    peak = 3.0 if 11 <= hour <= 14 else 1.0

                rows.append(
                    {
                        "station_id": str(station),
                        "prediction_time": (
                            start
                            + pd.Timedelta(days=day)
                            + pd.Timedelta(hours=hour)
                        ),
                        "departures": int(
                            rng.poisson(peak + 0.5)
                        ),
                    }
                )

    return pd.DataFrame(rows)


@pytest.mark.parametrize(
    ("family", "params"),
    [
        (
            "kmeans",
            {
                "n_clusters": 4,
                "n_init": 20,
                "max_iter": 300,
            },
        ),
        (
            "gmm",
            {
                "n_components": 3,
                "covariance_type": "diag",
                "n_init": 5,
                "max_iter": 300,
                "reg_covar": 1e-6,
            },
        ),
    ],
)
def test_p3_stability_supports_stage2_variants(family, params):
    frame = synthetic_daily_usage()

    station_ids = sorted(
        frame["station_id"].unique()
    )

    profiles = station_usage_profiles(
        frame,
        station_ids,
    )

    pipeline = build_p3_pipeline(
        family,
        params,
        seed=39,
    )
    pipeline.fit(profiles)

    reference_labels = pipeline.predict(profiles)

    scores = p3_stability_scores(
        frame,
        station_ids,
        profiles,
        reference_labels,
        family,
        params,
        seed=39,
        n_bootstraps=3,
    )

    assert len(scores) == 3
    assert all(np.isfinite(score) for score in scores)
    assert all(-1.0 <= score <= 1.0 for score in scores)


def test_p3_stability_rejects_invalid_bootstrap_count():
    frame = synthetic_daily_usage()
    station_ids = sorted(frame["station_id"].unique())

    profiles = station_usage_profiles(
        frame,
        station_ids,
    )

    pipeline = build_p3_pipeline(
        "kmeans",
        {
            "n_clusters": 3,
            "n_init": 20,
            "max_iter": 300,
        },
        seed=39,
    )
    pipeline.fit(profiles)

    with pytest.raises(ValueError, match="n_bootstraps"):
        p3_stability_scores(
            frame,
            station_ids,
            profiles,
            pipeline.predict(profiles),
            "kmeans",
            {
                "n_clusters": 3,
                "n_init": 20,
                "max_iter": 300,
            },
            n_bootstraps=0,
        )