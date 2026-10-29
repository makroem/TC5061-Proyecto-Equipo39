"""El ensayo no puede sobrescribir el origen ni resolver artefactos fuera de la copia."""
import sqlite3
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_tracking_migration import digest, logical_inventory, prepare, relocate_uri, restore_copy, validate_paths
from mibici_equipo39 import registry


@pytest.fixture
def old_store(tmp_path):
    source = tmp_path / "historical"
    source.mkdir()
    model = source / "mlruns" / "1" / "run1" / "artifacts" / "model"
    model.mkdir(parents=True)
    (model / "MLmodel").write_text("synthetic model metadata", encoding="utf-8")
    with sqlite3.connect(source / "mlflow.db") as db:
        db.executescript("""
            CREATE TABLE experiments (id INTEGER, name TEXT, artifact_location TEXT);
            CREATE TABLE runs (run_uuid TEXT, status TEXT, artifact_uri TEXT);
            CREATE TABLE model_versions (name TEXT, version INTEGER, source TEXT, storage_location TEXT);
            CREATE TABLE metrics (key TEXT, value REAL, run_uuid TEXT);
            CREATE TABLE registered_model_aliases (name TEXT, alias TEXT, version INTEGER);
        """)
        db.execute("INSERT INTO experiments VALUES (1, 'test', ?)", ((source / "mlruns/1").as_uri(),))
        db.execute("INSERT INTO runs VALUES ('run1', 'FINISHED', ?)", (model.parent.as_uri(),))
        db.execute("INSERT INTO model_versions VALUES ('p1', 1, ?, ?)", (model.as_uri(), model.as_uri()))
        db.execute("INSERT INTO metrics VALUES ('test_mae', 1.5, 'run1')")
        db.execute("INSERT INTO registered_model_aliases VALUES ('p1', 'champion', 1)")
    return source


def test_copy_preserves_original_and_relocates_artifacts(old_store, tmp_path):
    original_hash = digest(old_store / "mlflow.db")
    destination = tmp_path / "rehearsal"
    summary = prepare(old_store, destination)
    assert summary["source_unchanged"] and summary["logical_content_preserved"]
    assert summary["artifact_files"] == 1
    with sqlite3.connect(destination / "candidate/mlflow.db") as db:
        uri = db.execute("SELECT source FROM model_versions").fetchone()[0]
        assert uri.startswith((destination / "candidate").as_uri())
        db.execute("UPDATE metrics SET value=99")
    assert digest(old_store / "mlflow.db") == original_hash
    assert digest(destination / "backup/mlflow.db") == summary["backup_db_sha256"]
    assert logical_inventory(destination / "backup/mlflow.db") == logical_inventory(old_store / "mlflow.db")


def test_destination_cannot_overlap_or_overwrite(old_store, tmp_path):
    for target in (old_store, old_store / "nested", tmp_path):
        with pytest.raises(ValueError, match="solaparse"):
            validate_paths(old_store, target)
    existing = tmp_path / "existing"
    existing.mkdir()
    with pytest.raises(FileExistsError):
        validate_paths(old_store, existing)


def test_external_and_remote_artifacts_are_rejected(old_store, tmp_path):
    for uri in ((tmp_path / "outside").as_uri(), "https://example.org/model", "mlflow-artifacts:/../../outside"):
        with pytest.raises(ValueError):
            relocate_uri(uri, old_store, tmp_path / "copy")


def test_registry_uses_recorded_uri_and_keeps_legacy_support(monkeypatch):
    from types import SimpleNamespace
    tags = {"artifact_contract": "3", "model_uri": "models:/m-test"}
    monkeypatch.setattr(registry.mlflow, "MlflowClient", lambda: SimpleNamespace(
        get_run=lambda _: SimpleNamespace(data=SimpleNamespace(tags=tags))))
    assert registry.model_uri_for_run("run1") == "models:/m-test"
    tags.clear()
    assert registry.model_uri_for_run("run1") == "runs:/run1/model"
    tags["artifact_contract"] = "3"
    with pytest.raises(ValueError, match="no tiene model_uri"):
        registry.model_uri_for_run("run1")


def test_restore_uses_unchanged_backup_and_refuses_a_second_restore(old_store, tmp_path):
    destination = tmp_path / "rehearsal"
    prepare(old_store, destination)
    assert restore_copy(destination)["logical_content_preserved"]
    with pytest.raises(FileExistsError):
        restore_copy(destination)


def test_relocation_decodes_uri_only_once(old_store, tmp_path):
    path = old_store / "mlruns" / "nombre %20 con espacios"
    target = tmp_path / "copy"
    assert relocate_uri(path.as_uri(), old_store, target) == (target / path.relative_to(old_store)).as_uri()
