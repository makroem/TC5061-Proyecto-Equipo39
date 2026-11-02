"""Linaje del registro y seguridad de la llamada a Git; sin almacén de MLflow ni datos reales."""

from types import SimpleNamespace

import pytest

from mibici_equipo39 import registry
from mibici_equipo39.modeling import stage2, tracking

SELECTED = {"variant": "p2_lr_0.1", "run_id": "seleccionada"}


def run(run_id="seleccionada", status="FINISHED", **tags):
    base = {"delivery": stage2.DELIVERY, "question": "p2", "git_dirty": "false",
            "data_version": "dv", "split_version": "3", "variant_id": "p2_lr_0.1"}
    return SimpleNamespace(info=SimpleNamespace(run_id=run_id, status=status),
                           data=SimpleNamespace(tags={**base, **tags}))


@pytest.fixture
def manifests(monkeypatch):
    monkeypatch.setattr(registry, "current_versions", lambda: ("dv", "3"))
    monkeypatch.setattr(registry, "read_selection", lambda question: SELECTED)


def test_only_the_selected_run_or_its_reproduction_can_be_registered(manifests):
    reproduction = run("otra", stage_of_work="reproduce", reproduces_run_id="seleccionada")

    assert registry.check_run(run(), "p2") == "official"
    assert registry.check_run(reproduction, "p2") == "reproduction"


def test_every_lineage_problem_is_reported_before_registering(manifests):
    bad = run("otra", status="FAILED", delivery="A5", question="p1", git_dirty="true",
              data_version="vieja", stage_of_work="reproduce", reproduces_run_id="otra")

    with pytest.raises(ValueError) as error:
        registry.check_run(bad, "p2")

    message = str(error.value)
    for problem in ["no pertenece a la entrega", "es de la pregunta p1", "su estado es FAILED",
                    "cambios sin commit", "data_version o split_version",
                    "ni una reproducción de ella"]:
        assert problem in message


def test_a_reproduction_of_another_variant_is_rejected(manifests):
    other = run("otra", stage_of_work="reproduce", reproduces_run_id="seleccionada",
                variant_id="p2_lr_10")

    with pytest.raises(ValueError, match="ni una reproducción"):
        registry.check_run(other, "p2")


@pytest.mark.parametrize("got, expected, same", [
    ({"kind": "frame", "columns": ["a"], "data": [[1.0]]},
     {"kind": "frame", "columns": ["a"], "data": [[1.0 + 1e-12]]}, True),
    ({"kind": "frame", "columns": ["a"], "data": [[float("nan")]]},
     {"kind": "frame", "columns": ["a"], "data": [[float("nan")]]}, True),
    ({"kind": "frame", "columns": ["a"], "data": [[1.0]]},
     {"kind": "frame", "columns": ["b"], "data": [[1.0]]}, False),
    ({"kind": "array", "data": [1.0, 2.0]}, {"kind": "array", "data": [1.0]}, False),
    ({"kind": "array", "data": [1.0]}, {"kind": "frame", "data": [1.0]}, False),
    ({"kind": "array", "data": ["a", "b"]}, {"kind": "array", "data": ["a", "c"]}, False),
])
def test_load_check_compares_kind_columns_shape_and_values(got, expected, same):
    assert registry.same_prediction(got, expected) is same


def test_git_is_called_with_an_argument_list_and_without_a_shell(monkeypatch):
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0, stdout="a" * 40 if "rev-parse" in args else "")

    monkeypatch.setattr(tracking.subprocess, "run", fake_run)

    assert tracking.git_state() == ("a" * 40, False)
    assert [args[:2] for args, _ in calls] == [["git", "rev-parse"], ["git", "status"]]
    assert all(not kwargs.get("shell") and kwargs.get("check") is False for _, kwargs in calls)


@pytest.mark.parametrize("output", ["", "no-es-un-commit", "A" * 40, "a" * 39])
def test_git_output_that_is_not_a_commit_is_rejected(monkeypatch, output):
    monkeypatch.setattr(tracking.subprocess, "run",
                        lambda args, **kwargs: SimpleNamespace(returncode=0, stdout=output))

    with pytest.raises(RuntimeError, match="commit válido"):
        tracking.git_state()
