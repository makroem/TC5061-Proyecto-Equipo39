import numpy as np
import pandas as pd
import pytest
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.pipeline import Pipeline

from mibici_equipo39.modeling.p3 import build_p3_pipeline, cluster_metrics


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