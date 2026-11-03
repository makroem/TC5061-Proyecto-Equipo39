"""Paquete ficticio para comprobar integridad sin deserializar ni usar el Registry oficial."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

from mlflow.models import Model, ModelSignature
from mlflow.types.schema import Schema, ColSpec
import pytest

from mibici_equipo39.serving import export_model as exporter
from mibici_equipo39.serving.model_loader import inventory, bundle_digest


@pytest.fixture
def package(tmp_path, monkeypatch):
    folder = tmp_path / "source"
    folder.mkdir()
    run_id = "a" * 32
    signature = ModelSignature(inputs=Schema([ColSpec("double", "x")]),
                               outputs=Schema([ColSpec("double")]))
    model = Model(run_id=run_id, signature=signature, flavors={
        "python_function": {"loader_module": "mlflow.sklearn", "model_path": "model.pkl"}})
    model.save(str(folder / "MLmodel"))
    (folder / "model.pkl").write_bytes(b"not-a-real-serialized-model")
    files = inventory(folder)
    manifest = {"schema_version": 1, "model_name": "fixture-p1", "model_version": "1",
                "source_run_id": run_id, "training_commit": "b" * 40,
                "data_version": "c" * 64, "resolved_alias": "champion",
                "signature": signature.to_dict(), "files": files,
                "bundle_sha256": bundle_digest(files)}
    manifest_path = tmp_path / "approved.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    version = SimpleNamespace(name="fixture-p1", version="1", status="READY", run_id=run_id,
                              tags={"data_version": "c" * 64})
    run = SimpleNamespace(data=SimpleNamespace(tags={"git_commit": "b" * 40},
                                               params={"data_version": "c" * 64}))
    client = Mock()
    client.get_model_version_by_alias.return_value = version
    client.get_model_version.return_value = version
    client.get_run.return_value = run
    monkeypatch.setattr(exporter, "MlflowClient", lambda **kwargs: client)
    downloader = Mock(return_value=str(folder))
    monkeypatch.setattr(exporter.mlflow.artifacts, "download_artifacts", downloader)
    monkeypatch.setenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
    return SimpleNamespace(folder=folder, manifest=manifest, path=manifest_path,
                           client=client, downloader=downloader, version=version, run=run)
