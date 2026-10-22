"""Pruebas del contrato común sin datos de MiBici ni corridas oficiales."""
import json
import os
from pathlib import Path
import subprocess
import sys

import mlflow
import numpy as np
import pandas as pd
import pytest
from sklearn.dummy import DummyRegressor

from mibici_equipo39 import config as C
from mibici_equipo39.modeling.tracking import log_candidate_artifacts


@pytest.fixture
def contract(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "ROOT", tmp_path)
    monkeypatch.setattr(C, "REFERENCES", tmp_path)
    (tmp_path / "requirements.txt").write_text("mlflow==2.22.0\nscikit-learn==1.6.1\n")
    (tmp_path / "mibici_equipo39").mkdir()
    (tmp_path / "mibici_equipo39/__init__.py").write_text("")
    (tmp_path / "data_manifest.json").write_text(json.dumps({"data_version": "fixture"}))
    (tmp_path / "split_manifest.json").write_text(json.dumps({
        "data_version": "fixture", "split_id": "fixture-split", "version": "3"}))
    previous = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri((tmp_path / "tracking").as_uri())
    mlflow.set_experiment("prueba-contrato-no-oficial")
    X = pd.DataFrame({"hour": [8.0, 9.0], "month": [1.0, 1.0]})
    model = DummyRegressor().fit(X, [1.0, 3.0])
    yield tmp_path, X, model
    mlflow.set_tracking_uri(previous)


def test_model_loads_in_another_process_with_manifests_and_signature(contract):
    folder, X, model = contract
    plot = folder / "plot.txt"
    plot.write_text("Solo prueba de transporte de artefactos; no es una figura oficial.")
    with mlflow.start_run() as run:
        uri = log_candidate_artifacts(model, X, {"seed": 39}, plots=[plot],
                                      evaluation={"val_mae": 1.0})
    client = mlflow.MlflowClient()
    assert {a.path for a in client.list_artifacts(run.info.run_id)} == {
        "model", "config", "data", "plots", "evaluation"}
    saved = mlflow.artifacts.download_artifacts(uri)
    metadata = mlflow.models.Model.load(str(Path(saved) / "MLmodel"))
    assert metadata.signature is not None
    assert metadata.saved_input_example_info is not None
    example = folder / "input.json"
    X.to_json(example, orient="split")
    code = ("import json,sys,mlflow,pandas as pd; "
            "m=mlflow.pyfunc.load_model(sys.argv[1]); "
            "x=pd.read_json(sys.argv[2],orient='split').astype(float); "
            "print(json.dumps(m.predict(x).tolist()))")
    result = subprocess.run([sys.executable, "-c", code, saved, str(example)],
                            cwd=folder, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    np.testing.assert_allclose(json.loads(result.stdout), model.predict(X))
    assert client.get_run(run.info.run_id).data.tags["split_id"] == "fixture-split"


@pytest.mark.parametrize("column", ["user_id", "correo", "trip_id"])
def test_personal_columns_rejected_before_logging(contract, column):
    _, X, model = contract
    with mlflow.start_run() as run:
        with pytest.raises(ValueError, match="personales"):
            log_candidate_artifacts(model, X.rename(columns={"hour": column}), {})
    assert not mlflow.MlflowClient().list_artifacts(run.info.run_id)


def test_inconsistent_manifests_and_secrets_rejected(contract):
    folder, X, model = contract
    with mlflow.start_run():
        with pytest.raises(ValueError, match="sensible"):
            log_candidate_artifacts(model, X, {"nested": {"api_token": "no-real-token"}})
        (folder / "split_manifest.json").write_text(json.dumps({"data_version": "different"}))
        with pytest.raises(ValueError, match="distintas"):
            log_candidate_artifacts(model, X, {})


def test_pyfunc_with_two_outputs_loads_in_another_process(contract):
    folder, X, model = contract

    class TwoHeads(mlflow.pyfunc.PythonModel):
        def predict(self, context, model_input, params=None):
            values = model.predict(model_input)
            return pd.DataFrame({"bikes": values > 1, "docks": values > 3})

    with mlflow.start_run():
        uri = log_candidate_artifacts(TwoHeads(), X, {"thresholds": [1, 3]}, flavor="pyfunc")
    saved = mlflow.artifacts.download_artifacts(uri)
    code = ("import json,sys,mlflow,pandas as pd; "
            "m=mlflow.pyfunc.load_model(sys.argv[1]); "
            "x=pd.DataFrame({'hour':[8.0,9.0],'month':[1.0,1.0]}); "
            "print(m.predict(x).to_json(orient='list'))")
    result = subprocess.run([sys.executable, "-c", code, saved], cwd=folder,
                            text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"bikes": [True, True], "docks": [False, False]}


def test_projects_parent_is_preserved_with_search_and_candidate_children(contract, monkeypatch):
    from mibici_equipo39.modeling import tracking
    monkeypatch.setattr(tracking, "setup", lambda: None)
    with mlflow.start_run() as run:
        parent_id = run.info.run_id
    monkeypatch.setenv("MLFLOW_RUN_ID", parent_id)
    with tracking.question_run("busqueda-de-prueba") as search:
        with tracking.question_run("candidato-de-prueba") as child:
            assert child.data.tags["mlflow.parentRunId"] == search.info.run_id
        assert os.environ["MLFLOW_RUN_ID"] == parent_id
    assert mlflow.MlflowClient().get_run(search.info.run_id).data.tags["mlflow.parentRunId"] == parent_id
    assert os.environ["MLFLOW_RUN_ID"] == parent_id
