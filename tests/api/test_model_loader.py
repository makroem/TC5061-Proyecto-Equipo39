import json
from unittest.mock import Mock

import pytest

from mibici_equipo39.serving import model_loader as loader
from mibici_equipo39.serving.settings import Settings


def test_loads_only_after_verifying_package(package, monkeypatch):
    model = Mock()
    load = Mock(return_value=model)
    monkeypatch.setattr(loader.mlflow.pyfunc, "load_model", load)
    loaded = loader.load_model(package.folder, package.path)
    loaded.predict("frame")
    model.predict.assert_called_once_with("frame")
    assert loaded.manifest["model_version"] == "1"
    load.assert_called_once()


@pytest.mark.parametrize("change", ["modified", "missing", "extra"])
def test_corruption_is_rejected_before_deserialization(package, monkeypatch, change):
    load = Mock()
    monkeypatch.setattr(loader.mlflow.pyfunc, "load_model", load)
    if change == "missing":
        (package.folder / "model.pkl").unlink()
    elif change == "modified":
        (package.folder / "model.pkl").write_bytes(b"changed")
    else:
        (package.folder / "extra.txt").write_text("extra")
    with pytest.raises(ValueError, match="inventario"):
        loader.load_model(package.folder, package.path)
    load.assert_not_called()


@pytest.mark.parametrize("key,value", [
    ("schema_version", 2), ("model_version", "../1"), ("model_name", "../outside"),
    ("training_commit", None), ("source_run_id", "missing"), ("data_version", "unknown"),
    ("signature", None), ("bundle_sha256", "0" * 64),
])
def test_bad_manifest_fields(package, key, value):
    package.manifest[key] = value
    package.path.write_text(json.dumps(package.manifest))
    with pytest.raises(ValueError):
        loader.read_manifest(package.path)


@pytest.mark.parametrize("name", ["../outside", "/absolute", "C:/absolute", "x\\outside"])
def test_unsafe_manifest_path(package, name):
    package.manifest["files"][name] = "d" * 64
    package.manifest["bundle_sha256"] = loader.bundle_digest(package.manifest["files"])
    package.path.write_text(json.dumps(package.manifest))
    with pytest.raises(ValueError, match="Ruta"):
        loader.read_manifest(package.path)


def test_signature_and_run_checked(package):
    package.manifest["signature"]["inputs"] = "[]"
    with pytest.raises(ValueError, match="firma"):
        loader.verify_bundle(package.folder, package.manifest)
    package.manifest["signature"] = loader.package_metadata(package.folder).signature.to_dict()
    package.manifest["source_run_id"] = "e" * 32
    with pytest.raises(ValueError, match="run"):
        loader.verify_bundle(package.folder, package.manifest)


def test_missing_mlmodel(package):
    (package.folder / "MLmodel").unlink()
    with pytest.raises(ValueError, match="MLmodel"):
        loader.inventory(package.folder)


def test_settings_from_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("MODEL_DIR", str(tmp_path / "model"))
    monkeypatch.setenv("MODEL_MANIFEST", str(tmp_path / "manifest.json"))
    settings = Settings.from_env()
    assert settings.model_dir == tmp_path / "model"
    assert settings.model_manifest == tmp_path / "manifest.json"
