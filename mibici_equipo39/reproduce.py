"""Reproduce las selecciones versionadas y registra las corridas recién terminadas."""

import argparse
import json
import os
from pathlib import Path

import mlflow

from mibici_equipo39 import config as C
from mibici_equipo39.modeling import stage2, tracking


def validate_selections():
    """Comprueba las tres selecciones antes de descargar datos o entrenar."""
    data = json.loads((C.REFERENCES / "data_manifest.json").read_text(encoding="utf-8"))
    split = json.loads((C.REFERENCES / "split_manifest.json").read_text(encoding="utf-8"))
    selections = {}
    for question in C.REGISTERED_MODELS:
        selection = stage2.read_selection(question)
        required = {"variant", "family", "params", "run_id", "data_version", "split_id"}
        if required - selection.keys():
            raise ValueError(f"Selección incompleta de {question}: {sorted(required - selection.keys())}")
        if (selection["data_version"] != data["data_version"]
                or selection["split_id"] != split["split_id"]
                or split["data_version"] != data["data_version"]):
            raise ValueError(f"La selección de {question} no coincide con los manifiestos.")
        adapter = stage2.load_adapter(question)
        variants = [adapter.baseline(), *C.STAGE2_SEARCH_PLAN[question]]
        approved = {"name": selection["variant"], "family": selection["family"], "params": selection["params"]}
        if approved not in variants:
            raise ValueError(f"La selección de {question} no coincide con el plan versionado.")
        if not selection["run_id"]:
            raise ValueError(f"Falta la corrida de origen de {question}.")
        if adapter.needs_calibration:
            thresholds = selection.get("calibration", {}).get("thresholds", {})
            if (set(thresholds) != {"bikes", "docks"}
                    or any(not isinstance(v, (int, float)) or not 0 <= v <= 1 for v in thresholds.values())):
                raise ValueError(f"Falta la calibración congelada válida de {question}.")
        selections[question] = selection
    return selections


def launch(entry_point, parameters=None):
    """Cada paso conserva un identificador propio de MLflow Projects."""
    submitted = mlflow.projects.run(
        str(Path(__file__).resolve().parents[1]), entry_point=entry_point,
        parameters=parameters or {}, experiment_name=C.EXPERIMENT_NAME,
        env_manager="local", synchronous=True, run_name=f"A6-{entry_point}-reproduccion",
    )
    if submitted.get_status() != "FINISHED":
        raise RuntimeError(f"El paso {entry_point} no terminó correctamente.")
    return submitted.run_id


def selected_child(client, parent_id, question, selection):
    """Obtiene la hija del padre exacto; nunca busca la corrida global más reciente."""
    parent = client.get_run(parent_id)
    child_id = parent.data.tags.get("selected_run_id")
    if parent.info.status != "FINISHED" or not child_id:
        raise ValueError(f"La reproducción de {question} no publicó una selección terminada.")
    child = client.get_run(child_id)
    expected = {"mlflow.parentRunId": parent_id, "question": question,
                "stage_of_work": "reproduce", "variant_id": selection["variant"],
                "reproduces_run_id": selection["run_id"], "data_version": selection["data_version"]}
    if child.info.status != "FINISHED" or any(child.data.tags.get(k) != v for k, v in expected.items()):
        raise ValueError(f"La corrida hija de {question} no corresponde a esta reproducción.")
    return child_id


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--member", default="config")
    args = parser.parse_args(argv)
    member = stage2.resolve_member(args.member)
    workflow_id = os.environ.pop("MLFLOW_RUN_ID", None)
    if not workflow_id:
        raise RuntimeError("Ejecuta este flujo con mlflow run . -e reproduce.")
    commit, dirty = tracking.git_state()
    if dirty:
        raise RuntimeError("Hay cambios sin commit; la reproducción requiere un clon limpio.")
    mlflow.set_tracking_uri(C.TRACKING_URI)
    mlflow.set_registry_uri(C.REGISTRY_URI)
    client = mlflow.MlflowClient()
    parent = client.get_run(workflow_id)
    if client.get_experiment(parent.info.experiment_id).name != C.EXPERIMENT_NAME:
        raise ValueError(f"Usa --experiment-name {C.EXPERIMENT_NAME}.")
    with mlflow.start_run(run_id=workflow_id):
        selections = validate_selections()
        mlflow.set_tags({"team": C.TEAM, "delivery": "A6", "executor": member,
                         "stage_of_work": "reproduction_workflow", "git_commit": commit})
        mlflow.log_dict(selections, "config/approved_selection.json")
        steps = {"ingest": launch("ingest"), "questions": {}}
        # Primero se reproducen las tres preguntas. Un fallo de entrenamiento no cambia los alias.
        for question, selection in selections.items():
            parent_id = launch("train", {"question": question, "member": member,
                                         "model": "selected", "mode": "reproduce"})
            steps["questions"][question] = {
                "parent_run_id": parent_id,
                "source_run_id": selected_child(client, parent_id, question, selection),
            }
        for question, entry in steps["questions"].items():
            entry["registry_run_id"] = launch("registry", {
                "question": question, "source_run_id": entry["source_run_id"]})
        steps["verification_run_id"] = launch("verify_registry")
        result = {"workflow_run_id": workflow_id, "git_commit": commit, "status": "FINISHED", **steps}
        mlflow.log_dict(result, "evaluation/reproduction.json")
        folder = C.RESULTS_DIR / "stage2"
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"workflow_{workflow_id}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps(result, indent=2))
        return result


if __name__ == "__main__":
    main()
