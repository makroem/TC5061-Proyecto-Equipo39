"""Registro y carga por alias con un almacén temporal; no asigna champion en el servidor oficial."""

import os
from pathlib import Path
import subprocess
import sys

import mlflow
import pytest

from mibici_equipo39 import config as C
from mibici_equipo39 import registry
from mibici_equipo39.modeling import stage2

NAME = C.REGISTERED_MODELS["p1"]
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def searched(stage2_env):
    parent_id = stage2_env.project_run()
    summary = stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    children = stage2_env.children(parent_id)
    selected = children[summary["selected_variant"]]
    stage2_env.select(selected)
    return stage2_env, selected, children


def test_register_assigns_champion_after_the_load_check(searched):
    env, selected, _ = searched
    entry = registry.register("p1", selected.info.run_id)
    version = env.client.get_model_version_by_alias(NAME, C.MODEL_ALIAS)
    assert str(version.version) == entry["version"] == "1"
    assert version.run_id == selected.info.run_id
    assert version.tags["source_kind"] == "official" and version.tags["data_version"] == "fixture"
    assert env.client.get_registered_model(NAME).description
    assert (C.RESULTS_DIR / "stage2" / "registry_summary.json").is_file()


def test_a_run_that_was_not_selected_is_rejected(searched):
    env, selected, children = searched
    other = next(r for name, r in children.items() if r.info.run_id != selected.info.run_id)
    with pytest.raises(ValueError, match="no es la corrida seleccionada"):
        registry.register("p1", other.info.run_id)
    assert not env.client.search_registered_models(filter_string=f"name = '{NAME}'")


def test_alias_is_not_assigned_when_the_prediction_differs(searched, monkeypatch):
    env, selected, _ = searched
    monkeypatch.setattr(registry, "same_prediction", lambda got, expected: False)
    with pytest.raises(ValueError, match="no reproduce"):
        registry.register("p1", selected.info.run_id)
    with pytest.raises(mlflow.exceptions.MlflowException):
        env.client.get_model_version_by_alias(NAME, C.MODEL_ALIAS)


def test_verify_loads_the_champion_in_a_new_process(searched):
    env, selected, _ = searched
    registry.register("p1", selected.info.run_id)
    environment = {**os.environ, "MLFLOW_TRACKING_URI": env.uri, "MLFLOW_REGISTRY_URI": env.uri}
    environment.pop("MLFLOW_RUN_ID", None)
    result = subprocess.run([sys.executable, "-m", "mibici_equipo39.registry", "verify", "--question", "p1"],
                            cwd=REPO, env=environment, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert '"status": "ok"' in result.stdout


def test_verify_fails_when_a_champion_is_missing(stage2_env):
    with pytest.raises(SystemExit) as error:
        registry.verify(["p1"])
    assert error.value.code == 1
