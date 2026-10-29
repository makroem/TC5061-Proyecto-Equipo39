"""Entorno pequeño para probar el controlador y el registro de la etapa 2 sin datos de MiBici."""

import json
from types import SimpleNamespace

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error

from mibici_equipo39 import config as C
from mibici_equipo39.modeling import stage2, tracking

PLAN = [
    {"name": "ridge_01", "family": "ridge", "params": {"alpha": 0.1}},
    {"name": "ridge_10", "family": "ridge", "params": {"alpha": 10.0}},
    {"name": "ridge_1000", "family": "ridge", "params": {"alpha": 1000.0}},
]
PREFIX = {"train": "train", "validation": "val", "test": "test"}


def pytest_collection_modifyitems(items):
    """Separa las pruebas que usan HTTP local o un almacén temporal de MLflow."""
    local_services = {"source", "contract", "stage2_env"}
    for item in items:
        if local_services.intersection(item.fixturenames):
            item.add_marker(pytest.mark.integration)


class FakeAdapter(stage2.QuestionAdapter):
    question, selection_metric, greater_is_better = "p1", "val_mae", False

    def baseline(self):
        return {"name": "baseline", "family": "dummy", "params": {"strategy": "mean"}}

    def load_data(self):
        rng = np.random.default_rng(39)
        X = pd.DataFrame({"hour_of_day": rng.integers(0, 24, 90).astype(float),
                          "month": rng.integers(1, 13, 90).astype(float)})
        y = 2 * X["hour_of_day"] + rng.normal(0, 1, 90)
        split = np.array(["train"] * 60 + ["validation"] * 15 + ["test"] * 15)
        return {"X": X, "y": y, "split": split}

    def fit(self, variant, data):
        train = data["split"] == "train"
        estimator = DummyRegressor if variant["family"] == "dummy" else Ridge
        model = estimator(**variant["params"]).fit(data["X"][train], data["y"][train])
        return stage2.Fitted(variant, model, "sklearn")

    def evaluate(self, fitted, data, split):
        mask = data["split"] == split
        mae = mean_absolute_error(data["y"][mask], fitted.model.predict(data["X"][mask]))
        return {f"{PREFIX[split]}_mae": float(mae)}

    def input_example(self, fitted, data):
        return data["X"].head(3)

    def plots(self, fitted, data, folder):
        path = folder / "real_vs_predicho.png"
        fig, ax = plt.subplots()
        ax.plot([0, 1], [0, 1])
        fig.savefig(path)
        plt.close(fig)
        return [path]


@pytest.fixture
def stage2_env(tmp_path, monkeypatch):
    """Almacén SQLite temporal, manifiestos de prueba y un padre que imita a mlflow run."""
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    for key, value in {"ROOT": tmp_path, "REFERENCES": tmp_path, "RESULTS_DIR": tmp_path / "results",
                       "TRACKING_URI": uri, "REGISTRY_URI": uri,
                       "EXPERIMENT_NAME": "prueba-etapa2-no-oficial"}.items():
        monkeypatch.setattr(C, key, value)
    monkeypatch.setattr(C, "STAGE2_SEARCH_PLAN", {"p1": PLAN})
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    monkeypatch.setenv("MLFLOW_REGISTRY_URI", uri)
    (tmp_path / "requirements.txt").write_text(f"mlflow=={mlflow.__version__}\nscikit-learn==1.6.1\n")
    (tmp_path / "mibici_equipo39").mkdir()
    (tmp_path / "mibici_equipo39/__init__.py").write_text("")
    (tmp_path / "etapa2").mkdir()
    (tmp_path / "data_manifest.json").write_text(json.dumps({"data_version": "fixture"}))
    (tmp_path / "split_manifest.json").write_text(json.dumps({
        "data_version": "fixture", "split_id": "fixture-split", "version": "3",
        "strategy": "chronological_holdout"}))
    (tmp_path / "etapa2/starting_point.json").write_text(json.dumps({"models": [
        {"run_id": "historico-p1", "question": "P1", "role": "baseline"}]}))
    monkeypatch.setattr(tracking, "git_state", lambda: ("a" * 40, False))
    monkeypatch.setattr(stage2, "load_adapter", lambda question: FakeAdapter())

    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(uri)
    client = mlflow.MlflowClient()
    experiment_id = client.create_experiment(
        C.EXPERIMENT_NAME, artifact_location=(tmp_path / "artifacts").as_uri())

    def project_run():
        run_id = client.create_run(experiment_id).info.run_id
        monkeypatch.setenv("MLFLOW_RUN_ID", run_id)
        return run_id

    def children(parent_id):
        runs = client.search_runs([experiment_id], f"tags.mlflow.parentRunId = '{parent_id}'")
        return {r.data.tags["variant_id"]: r for r in runs}

    def select(variant_run):
        tags = variant_run.data.tags
        variant = next(v for v in [FakeAdapter().baseline(), *PLAN] if v["name"] == tags["variant_id"])
        (tmp_path / "etapa2/selection.json").write_text(json.dumps({"p1": {
            **variant, "variant": variant["name"], "run_id": variant_run.info.run_id}}))

    yield SimpleNamespace(path=tmp_path, uri=uri, client=client, project_run=project_run,
                          children=children, select=select)
