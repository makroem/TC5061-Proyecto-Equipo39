import json

import pytest

from mibici_equipo39.serving.export_model import export_model
from mibici_equipo39.serving.model_loader import read_manifest, verify_bundle


def test_first_export_pins_numeric_version(package, tmp_path):
    output, manifest = tmp_path / "output", tmp_path / "published.json"
    result = export_model(name="fixture-p1", alias="champion", output=output,
                          manifest_out=manifest)
    package.client.get_model_version_by_alias.assert_called_once_with("fixture-p1", "champion")
    assert package.downloader.call_args.kwargs["artifact_uri"] == "models:/fixture-p1/1"
    assert result == read_manifest(manifest)
    verify_bundle(output, result)
    assert "http:" not in manifest.read_text()


def test_reproduction_does_not_resolve_alias(package, tmp_path):
    result = export_model(manifest=package.path, output=tmp_path / "output")
    package.client.get_model_version.assert_called_once_with("fixture-p1", "1")
    package.client.get_model_version_by_alias.assert_not_called()
    assert result == package.manifest


def test_existing_matching_package_is_verified_without_download(package):
    result = export_model(manifest=package.path, output=package.folder)
    package.downloader.assert_not_called()
    assert result == package.manifest


def test_existing_unknown_package_is_not_overwritten(package):
    original = (package.folder / "model.pkl").read_bytes()
    with pytest.raises(FileExistsError):
        export_model(name="fixture-p1", output=package.folder)
    assert (package.folder / "model.pkl").read_bytes() == original


def test_missing_version_does_not_leave_destination(package, tmp_path):
    package.client.get_model_version.side_effect = RuntimeError("version missing")
    output = tmp_path / "output"
    with pytest.raises(RuntimeError, match="version missing"):
        export_model(manifest=package.path, output=output)
    assert not output.exists()
    package.downloader.assert_not_called()


def test_changed_registry_lineage_rejected(package, tmp_path):
    package.version.run_id = "d" * 32
    with pytest.raises(ValueError, match="linaje"):
        export_model(manifest=package.path, output=tmp_path / "output")
    package.downloader.assert_not_called()


def test_truncated_download_rejected(package, tmp_path):
    (package.folder / "model.pkl").unlink()
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="Falta archivo"):
        export_model(name="fixture-p1", output=output, manifest_out=tmp_path / "result.json")
    assert not output.exists()
    assert not (tmp_path / "result.json").exists()


def test_changed_download_rejected(package, tmp_path):
    (package.folder / "model.pkl").write_bytes(b"wrong")
    with pytest.raises(ValueError, match="inventario"):
        export_model(manifest=package.path, output=tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_missing_tracking_is_not_replaced_by_empty_database(package, monkeypatch, tmp_path):
    monkeypatch.delenv("MLFLOW_TRACKING_URI")
    with pytest.raises(ValueError, match="MLFLOW_TRACKING_URI"):
        export_model(manifest=package.path, output=tmp_path / "output")


def test_replay_does_not_accept_alias(package, tmp_path):
    with pytest.raises(ValueError, match="alias"):
        export_model(manifest=package.path, alias="champion", output=tmp_path / "output")


def test_manifest_cannot_be_written_inside_package(package, tmp_path):
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="fuera"):
        export_model(name="fixture-p1", output=output, manifest_out=output / "manifest.json")


def test_pending_version_rejected(package, tmp_path):
    package.version.status = "PENDING_REGISTRATION"
    with pytest.raises(ValueError, match="lista"):
        export_model(manifest=package.path, output=tmp_path / "output")
