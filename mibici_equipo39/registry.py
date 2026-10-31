"""Registro de los modelos seleccionados y verificación de su carga por alias."""

import argparse
import json
from pathlib import Path

import mlflow
from mlflow.exceptions import MlflowException
import numpy as np

from mibici_equipo39 import config as C
from mibici_equipo39.modeling.stage2 import DELIVERY, read_selection, to_jsonable

DESCRIPTIONS = {
    "p1": "P1 demanda: viajes que inician por estación en la siguiente hora, para planear flota.",
    "p2": ("P2 riesgo aproximado: probabilidad y alerta de falta de bicicletas y de anclajes en la "
           "siguiente hora. Etiquetas derivadas de viajes y capacidad publicada, sin inventario observado."),
    "p3": "P3 grupos: asignación de estaciones a perfiles horarios de uso, para análisis de planeación.",
}
LIFECYCLE = "Producción académica: el alias champion identifica la versión elegida; no es un servicio desplegado."


def connect():
    mlflow.set_tracking_uri(C.TRACKING_URI)
    mlflow.set_registry_uri(C.REGISTRY_URI)
    return mlflow.MlflowClient()


def current_versions():
    data = json.loads((C.REFERENCES / "data_manifest.json").read_text(encoding="utf-8"))
    split = json.loads((C.REFERENCES / "split_manifest.json").read_text(encoding="utf-8"))
    return data["data_version"], split["version"]


def check_run(run, question):
    """Devuelve 'official' o 'reproduction'; falla si la corrida no es la selección aprobada."""
    tags = run.data.tags
    data_version, split_version = current_versions()
    problems = []
    if tags.get("delivery") != DELIVERY:
        problems.append(f"no pertenece a la entrega {DELIVERY}")
    if tags.get("question") != question:
        problems.append(f"es de la pregunta {tags.get('question')}, no de {question}")
    if run.info.status != "FINISHED":
        problems.append(f"su estado es {run.info.status}")
    if tags.get("git_dirty") != "false":
        problems.append("se ejecutó con cambios sin commit")
    if tags.get("data_version") != data_version or tags.get("split_version") != split_version:
        problems.append("data_version o split_version no coinciden con los manifiestos actuales")
    selection = read_selection(question)
    if run.info.run_id == selection.get("run_id"):
        kind = "official"
    elif (tags.get("stage_of_work") == "reproduce" and tags.get("variant_id") == selection.get("variant")
          and tags.get("reproduces_run_id") == selection.get("run_id")):
        kind = "reproduction"
    else:
        kind = None
        problems.append("no es la corrida seleccionada ni una reproducción de ella")
    if problems:
        raise ValueError(f"La corrida {run.info.run_id} no se puede registrar: " + "; ".join(problems) + ".")
    return kind


def model_uri_for_run(run_id):
    """Usa la URI registrada por MLflow 3 o la ubicación histórica de MLflow 2."""
    tags = mlflow.MlflowClient().get_run(run_id).data.tags
    if tags.get("artifact_contract") == "3" and not tags.get("model_uri"):
        raise ValueError(f"La corrida {run_id} declara contrato 3 pero no tiene model_uri.")
    return tags.get("model_uri") or f"runs:/{run_id}/model"


def load_example(run_id):
    local = Path(mlflow.artifacts.download_artifacts(model_uri_for_run(run_id)))
    metadata = mlflow.models.Model.load(str(local / "MLmodel"))
    if metadata.signature is None:
        raise ValueError(f"El modelo de {run_id} no tiene firma.")
    example = metadata.load_input_example(str(local))
    expected = mlflow.artifacts.load_dict(f"runs:/{run_id}/evaluation/example_prediction.json")
    return example, expected


def same_prediction(got, expected):
    if got["kind"] != expected["kind"] or got.get("columns") != expected.get("columns"):
        return False
    a, b = np.asarray(got["data"], dtype=object), np.asarray(expected["data"], dtype=object)
    if a.shape != b.shape:
        return False
    try:
        return bool(np.allclose(a.astype(float), b.astype(float), equal_nan=True))
    except (TypeError, ValueError):
        return bool((a == b).all())


def check_load(model_uri, example, expected):
    """Carga en este proceso y compara con la predicción guardada durante el entrenamiento."""
    got = to_jsonable(mlflow.pyfunc.load_model(model_uri).predict(example))
    if not same_prediction(got, expected):
        raise ValueError(f"{model_uri} no reproduce la predicción guardada del ejemplo.")


def save_summary(question, entry):
    path = C.RESULTS_DIR / "stage2" / "registry_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    summary = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    summary[question] = entry
    path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def register(question, source_run_id):
    client = connect()
    run = client.get_run(source_run_id)
    kind = check_run(run, question)
    example, expected = load_example(source_run_id)
    name = C.REGISTERED_MODELS[question]
    if not client.search_registered_models(filter_string=f"name = '{name}'"):
        client.create_registered_model(name, description=f"{DESCRIPTIONS[question]} {LIFECYCLE}")
    version = str(mlflow.register_model(model_uri_for_run(source_run_id), name).version)
    tags = run.data.tags
    lineage = {"source_run_id": source_run_id, "source_kind": kind, "variant_id": tags.get("variant_id", ""),
               "git_commit": tags.get("git_commit", ""), "data_version": tags.get("data_version", ""),
               "split_version": tags.get("split_version", ""), "delivery": DELIVERY}
    for key, value in lineage.items():
        client.set_model_version_tag(name, version, key, value)
    client.update_model_version(name, version, description=(
        f"{lineage['variant_id']} ({kind}). Corrida {source_run_id}, commit {lineage['git_commit'][:7]}, "
        f"data_version {lineage['data_version'][:12]}, split_version {lineage['split_version']}."))
    # El alias se asigna solo después de comprobar que la versión carga y predice igual.
    check_load(f"models:/{name}/{version}", example, expected)
    client.set_registered_model_alias(name, C.MODEL_ALIAS, version)
    entry = {"name": name, "version": version, "alias": C.MODEL_ALIAS, **lineage, "load_check": "ok"}
    save_summary(question, entry)
    print(json.dumps(entry, indent=2))
    return entry


def verify(questions):
    client = connect()
    results, failed = {}, False
    for question in questions:
        name = C.REGISTERED_MODELS[question]
        uri = f"models:/{name}@{C.MODEL_ALIAS}"
        try:
            version = client.get_model_version_by_alias(name, C.MODEL_ALIAS)
            example, expected = load_example(version.run_id)
            check_load(uri, example, expected)
            results[question] = {"uri": uri, "version": str(version.version), "rows": len(example), "status": "ok"}
        except (MlflowException, ValueError, OSError, ImportError) as exc:
            failed = True
            results[question] = {"uri": uri, "status": f"error: {exc}"}
    print(json.dumps(results, indent=2, ensure_ascii=False))
    if failed:
        raise SystemExit(1)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description="Model Registry de la etapa 2")
    commands = parser.add_subparsers(dest="command", required=True)
    reg = commands.add_parser("register")
    reg.add_argument("--question", required=True, choices=list(C.REGISTERED_MODELS))
    reg.add_argument("--source-run-id", required=True)
    ver = commands.add_parser("verify")
    ver.add_argument("--question", choices=list(C.REGISTERED_MODELS))
    args = parser.parse_args(argv)
    if args.command == "register":
        return register(args.question, args.source_run_id)
    return verify([args.question] if args.question else list(C.REGISTERED_MODELS))


if __name__ == "__main__":
    main()
