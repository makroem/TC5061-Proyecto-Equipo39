"""Controles del flujo no interactivo y de su vínculo exacto con las corridas."""

from contextlib import nullcontext
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mibici_equipo39 import config as C, reproduce


@pytest.fixture
def selection_files(tmp_path, monkeypatch):
    source = Path(__file__).resolve().parents[1] / "references"
    (tmp_path / "etapa2").mkdir()
    for name in ["data_manifest.json", "split_manifest.json", "etapa2/selection.json"]:
        (tmp_path / name).write_bytes((source / name).read_bytes())
    monkeypatch.setattr(C, "REFERENCES", tmp_path)
    return tmp_path / "etapa2/selection.json"


def test_the_versioned_selections_need_no_manual_preparation(selection_files):
    approved = reproduce.validate_selections()
    assert set(approved) == {"p1", "p2", "p3"}
    assert approved["p2"]["calibration"]["thresholds"] == {"bikes": 0.65, "docks": 0.70}


@pytest.mark.parametrize("question,key,value", [
    ("p1", "data_version", "other-data"), ("p3", "split_id", "other-split"),
    ("p2", "calibration", {}), ("p2", "calibration", {"thresholds": {"bikes": 2, "docks": 0.7}}),
    ("p1", "params", {"unreviewed": True}), ("p1", "run_id", ""),
])
def test_inconsistent_selection_is_rejected(selection_files, question, key, value):
    data = json.loads(selection_files.read_text())
    data[question][key] = value
    selection_files.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        reproduce.validate_selections()


def runs_for_child():
    selection = {"variant": "baseline", "run_id": "original", "data_version": "data"}
    tags = {"mlflow.parentRunId": "parent", "question": "p1", "stage_of_work": "reproduce",
            "variant_id": "baseline", "reproduces_run_id": "original", "data_version": "data"}
    runs = {"parent": SimpleNamespace(info=SimpleNamespace(status="FINISHED"),
                                     data=SimpleNamespace(tags={"selected_run_id": "child"})),
            "child": SimpleNamespace(info=SimpleNamespace(status="FINISHED"), data=SimpleNamespace(tags=tags))}
    return selection, runs


def test_the_exact_parent_selects_the_child_without_a_global_search():
    selection, runs = runs_for_child()
    client = SimpleNamespace(get_run=lambda run_id: runs[run_id])
    assert reproduce.selected_child(client, "parent", "p1", selection) == "child"


@pytest.mark.parametrize("key,value", [("mlflow.parentRunId", "other-parent"), ("question", "p2"),
                                      ("reproduces_run_id", "other-source"), ("data_version", "other-data")])
def test_a_foreign_child_cannot_be_registered(key, value):
    selection, runs = runs_for_child()
    runs["child"].data.tags[key] = value
    with pytest.raises(ValueError, match="no corresponde"):
        reproduce.selected_child(SimpleNamespace(get_run=lambda rid: runs[rid]), "parent", "p1", selection)


def test_a_failed_parent_cannot_provide_a_child():
    selection, runs = runs_for_child()
    runs["parent"].info.status = "FAILED"
    with pytest.raises(ValueError, match="terminada"):
        reproduce.selected_child(SimpleNamespace(get_run=lambda rid: runs[rid]), "parent", "p1", selection)


@pytest.mark.parametrize("failure", [None, "p2"])
def test_workflow_passes_generated_ids_and_stops_before_registry_on_training_failure(tmp_path, monkeypatch, failure):
    calls, records = [], []
    monkeypatch.setenv("MLFLOW_RUN_ID", "workflow")
    monkeypatch.setattr(C, "RESULTS_DIR", tmp_path)
    monkeypatch.setattr(reproduce.tracking, "git_state", lambda: ("a" * 40, False))
    monkeypatch.setattr(reproduce, "validate_selections", lambda: {q: {} for q in ("p1", "p2", "p3")})
    client = SimpleNamespace(get_run=lambda rid: SimpleNamespace(info=SimpleNamespace(experiment_id="1")),
                             get_experiment=lambda eid: SimpleNamespace(name=C.EXPERIMENT_NAME))
    monkeypatch.setattr(reproduce.mlflow, "MlflowClient", lambda: client)
    monkeypatch.setattr(reproduce.mlflow, "start_run", lambda **kw: nullcontext())
    monkeypatch.setattr(reproduce.mlflow, "set_tags", lambda tags: None)
    monkeypatch.setattr(reproduce.mlflow, "log_dict", lambda obj, path: records.append(copy.deepcopy(obj)))
    monkeypatch.setattr(reproduce, "selected_child", lambda client, pid, q, s: f"child-{pid}")

    def launch(entry, parameters=None):
        calls.append((entry, parameters))
        if entry == "train" and parameters["question"] == failure:
            raise RuntimeError("entrenamiento fallido")
        return f"{entry}-{len(calls)}"

    monkeypatch.setattr(reproduce, "launch", launch)
    if failure:
        with pytest.raises(RuntimeError, match="entrenamiento fallido"):
            reproduce.main(["--member", "Marco"])
        assert not any(entry == "registry" for entry, _ in calls)
        assert not list(tmp_path.rglob("workflow_*.json"))
    else:
        result = reproduce.main(["--member", "Marco"])
        assert [c[0] for c in calls] == ["ingest", "train", "train", "train", "registry", "registry", "registry", "verify_registry"]
        assert [p["source_run_id"] for e, p in calls if e == "registry"] == ["child-train-2", "child-train-3", "child-train-4"]
        assert result["status"] == "FINISHED" and records[-1] == result
        assert json.loads((tmp_path / "stage2/workflow_workflow.json").read_text()) == result
