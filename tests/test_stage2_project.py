"""Controlador de la etapa 2 con un adaptador falso; no son corridas oficiales."""

import json

import mlflow
import pytest

from mibici_equipo39.modeling import stage2, tracking


@pytest.mark.parametrize("argv", [
    ["--question", "p9"],
    ["--question", "p1", "--model", "rf"],
    ["--question", "p1", "--model", "selected"],
    ["--question", "p1", "--mode", "reproduce"],
])
def test_unknown_or_inconsistent_arguments_are_rejected(argv):
    with pytest.raises(SystemExit):
        stage2.parse_args(argv)


def test_member_must_be_a_known_person(monkeypatch):
    with pytest.raises(ValueError, match="member"):
        stage2.resolve_member("Pedro")
    monkeypatch.setenv("MIBICI_EXECUTOR", "Marco")
    assert stage2.resolve_member("config") == "Marco"


def test_hyperparameter_overrides_are_validated(stage2_env):
    adapter = stage2.load_adapter("p1")
    good = stage2_env.path / "overrides.json"
    good.write_text(json.dumps({"ridge_10": {"alpha": 5.0}}))
    variants = stage2.resolve_variants(adapter, "search", stage2.load_overrides(str(good)))
    assert [v["name"] for v in variants] == ["baseline", "ridge_01", "ridge_10", "ridge_1000"]
    assert next(v for v in variants if v["name"] == "ridge_10")["params"]["alpha"] == 5.0
    for bad in ({"ridge_99": {"alpha": 1}}, {"ridge_10": {"alfa": 1}}):
        good.write_text(json.dumps(bad))
        with pytest.raises(ValueError, match="desconocid"):
            stage2.resolve_variants(adapter, "search", stage2.load_overrides(str(good)))


def test_search_logs_baseline_and_three_nested_candidates(stage2_env):
    parent_id = stage2_env.project_run()
    summary = stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    children = stage2_env.children(parent_id)
    assert set(children) == {"baseline", "ridge_01", "ridge_10", "ridge_1000"}
    for name, run in children.items():
        tags = run.data.tags
        assert run.info.status == "FINISHED"
        assert tags["stage_of_work"] == ("baseline" if name == "baseline" else "candidate")
        assert tags["delivery"] == "A6" and tags["question"] == "p1" and tags["git_dirty"] == "false"
        assert {"train_mae", "val_mae", "test_mae", "fit_seconds"} <= set(run.data.metrics)
        folders = {a.path for a in stage2_env.client.list_artifacts(run.info.run_id)}
        assert {"model", "data", "config", "plots", "evaluation"} <= folders
    assert children["baseline"].data.tags["baseline_source_run_id"] == "historico-p1"
    parent = stage2_env.client.get_run(parent_id)
    assert parent.data.tags["stage_of_work"] == "search"
    assert parent.data.tags["selected_variant"] == summary["selected_variant"] != "baseline"
    assert children[summary["selected_variant"]].data.tags["selected"] == "true"


def test_selection_is_written_before_any_test_metric(stage2_env):
    parent_id = stage2_env.project_run()
    stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    selection = mlflow.artifacts.load_dict(f"runs:/{parent_id}/evaluation/selection_before_test.json")
    assert set(selection["validation_metrics"]) == {"baseline", "ridge_01", "ridge_10", "ridge_1000"}
    assert "test_" not in json.dumps(selection)


def test_a_tie_at_six_decimals_keeps_the_baseline():
    from conftest import FakeAdapter

    metrics = {"baseline": {"val_mae": 1.0000001}, "ridge_01": {"val_mae": 1.0}}
    assert stage2.select(FakeAdapter(), metrics)[0] == "baseline"


def test_requires_mlflow_run_and_a_clean_tree(stage2_env, monkeypatch):
    with pytest.raises(RuntimeError, match="mlflow run"):
        stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    stage2_env.project_run()
    monkeypatch.setattr(tracking, "git_state", lambda: ("a" * 40, True))
    with pytest.raises(RuntimeError, match="sin commit"):
        stage2.main(["--question", "p1", "--member", "DiegoMartinez"])


def test_reproduce_trains_only_the_selected_variant(stage2_env):
    search_id = stage2_env.project_run()
    summary = stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    selected = stage2_env.children(search_id)[summary["selected_variant"]]
    stage2_env.select(selected)
    parent_id = stage2_env.project_run()
    stage2.main(["--question", "p1", "--model", "selected", "--mode", "reproduce", "--member", "Marco"])
    children = stage2_env.children(parent_id)
    assert list(children) == [summary["selected_variant"]]
    tags = children[summary["selected_variant"]].data.tags
    assert tags["stage_of_work"] == "reproduce"
    assert tags["reproduces_run_id"] == selected.info.run_id
    assert children[summary["selected_variant"]].data.metrics["val_mae"] == pytest.approx(
        selected.data.metrics["val_mae"])


def test_adapter_extras_reach_config_and_evaluation(stage2_env, monkeypatch):
    from conftest import FakeAdapter

    class WithExtras(FakeAdapter):
        def fit(self, variant, data):
            fitted = super().fit(variant, data)
            fitted.extra = {"config": {"thresholds": {"bikes": 0.65}},
                            "evaluation": {"threshold_search": [{"threshold": 0.65}]}}
            return fitted

    monkeypatch.setattr(stage2, "load_adapter", lambda question: WithExtras())
    parent_id = stage2_env.project_run()
    stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    run_id = stage2_env.children(parent_id)["baseline"].info.run_id
    resolved = mlflow.artifacts.load_dict(f"runs:/{run_id}/config/resolved.json")
    summary = mlflow.artifacts.load_dict(f"runs:/{run_id}/evaluation/summary.json")
    assert resolved["thresholds"] == {"bikes": 0.65} and resolved["variant"]["name"] == "baseline"
    assert summary["threshold_search"] == [{"threshold": 0.65}] and "val_mae" in summary["metrics"]


def test_search_without_an_eligible_variant_stops_before_test(stage2_env, monkeypatch):
    from conftest import FakeAdapter

    splits = []

    class NoneEligible(FakeAdapter):
        def eligible(self, val_metrics):
            return False

        def evaluate(self, fitted, data, split):
            splits.append(split)
            return super().evaluate(fitted, data, split)

    monkeypatch.setattr(stage2, "load_adapter", lambda question: NoneEligible())
    parent_id = stage2_env.project_run()
    with pytest.raises(RuntimeError, match="antes de evaluar prueba"):
        stage2.main(["--question", "p1", "--member", "DiegoMartinez"])
    assert "test" not in splits and set(splits) == {"validation"}
    selection = mlflow.artifacts.load_dict(f"runs:/{parent_id}/evaluation/selection_before_test.json")
    assert selection["selected_variant"] is None
    parent = stage2_env.client.get_run(parent_id)
    assert parent.info.status == "FAILED" and parent.data.tags["search_status"] == "sin_ganador_elegible"
    assert stage2_env.children(parent_id) == {}
