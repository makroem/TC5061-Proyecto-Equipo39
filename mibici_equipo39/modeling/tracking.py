from contextlib import contextmanager
import json
import os
from pathlib import Path
import platform
import subprocess
import tempfile

import mlflow
import sklearn

from mibici_equipo39 import config as C


def git_state():
    def git(*args):
        try:
            result = subprocess.run(
                ["git", *args], cwd=C.ROOT, capture_output=True, text=True, check=False
            )
        except OSError as exc:
            raise RuntimeError("No fue posible comprobar Git; no se puede registrar un run trazable.") from exc
        if result.returncode:
            raise RuntimeError("Falló la comprobación de Git; no se puede declarar el repositorio limpio.")
        return result.stdout.strip()

    commit = git("rev-parse", "HEAD")
    if len(commit) not in (40, 64) or any(c not in "0123456789abcdef" for c in commit):
        raise RuntimeError("Git no devolvió un commit válido para el run.")
    return commit, bool(git("status", "--porcelain", "--untracked-files=normal"))


def common_params(metadata):
    data = json.loads((C.REFERENCES / "data_manifest.json").read_text())
    split = json.loads((C.REFERENCES / "split_manifest.json").read_text())
    rows = metadata["split"].value_counts()
    return {
        "data_version": data["data_version"],
        "source_start": C.SOURCE_START,
        "source_end_exclusive": C.SOURCE_END_EXCLUSIVE,
        "features_start": C.FEATURES_START,
        "split_strategy": split["strategy"],
        "split_id": split["split_id"],
        "seed": C.SEED,
        "cleaning_schema_version": C.CLEANING_SCHEMA_VERSION,
        "feature_schema_version": C.FEATURE_SCHEMA_VERSION,
        "horizon_minutes": 60,
        "n_stations": metadata["station_id"].nunique(),
        **{f"n_rows_{k}": int(v) for k, v in rows.items()},
        "python_version": platform.python_version(),
        "sklearn_version": sklearn.__version__,
    }


def common_tags(question, task_type, executor, code_author, target_definition):
    commit, dirty = git_state()
    return {
        "team": C.TEAM,
        "question": question,
        "task_type": task_type,
        "executor": executor,
        "code_author": code_author,
        "git_commit": commit,
        "git_dirty": str(dirty).lower(),
        "target_definition": target_definition,
    }


def setup():
    mlflow.set_tracking_uri(C.TRACKING_URI)
    mlflow.set_registry_uri(C.REGISTRY_URI)
    if mlflow.get_experiment_by_name(C.EXPERIMENT_NAME) is None:
        # El servidor HTTP decide el destino. Los experimentos existentes conservan el suyo.
        if C.TRACKING_URI.startswith(("http://", "https://")):
            mlflow.create_experiment(C.EXPERIMENT_NAME)
        else:
            mlflow.create_experiment(
                C.EXPERIMENT_NAME, artifact_location=(C.ROOT / "mlartifacts").as_uri()
            )
    mlflow.set_experiment(C.EXPERIMENT_NAME)


@contextmanager
def question_run(run_name):
    """Un run por modelo; dentro de `mlflow run` queda anidado bajo el run del proyecto."""
    setup()
    # MLflow relee MLFLOW_RUN_ID en cada start_run y reabriría al padre en lugar de crear el hijo.
    parent = os.environ.pop("MLFLOW_RUN_ID", None)
    try:
        if parent and mlflow.active_run() is None:
            with (
                mlflow.start_run(run_id=parent),
                mlflow.start_run(run_name=run_name, nested=True) as run,
            ):
                yield run
        else:
            with mlflow.start_run(
                run_name=run_name, nested=mlflow.active_run() is not None
            ) as run:
                yield run
    finally:
        if parent:
            os.environ["MLFLOW_RUN_ID"] = parent


def log_model_run(run_name, tags, params, metrics, texts=None, figures=()):
    """Registra un modelo: tags, parámetros, métricas, archivos de texto y figuras."""
    with question_run(run_name), tempfile.TemporaryDirectory() as tmp:
        mlflow.set_tags(tags)
        mlflow.log_params(params)
        mlflow.log_metrics(metrics)
        for name, text in (texts or {}).items():
            path = Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            mlflow.log_artifact(str(path))
        for figure in figures:
            mlflow.log_artifact(str(figure), "figures")


def log_candidate_artifacts(model, input_example, resolved_config, *,
                            flavor="sklearn", plots=(), evaluation=None,
                            manifest_paths=None):
    """Guarda un estimador completo dentro del run activo y devuelve su URI.

    El ejemplo debe ser pequeño y agregado, sin identificadores de viajes o usuarios.
    Para P2, el PythonModel incluye ambos clasificadores y los umbrales. Para P3,
    el estimador incluye el escalador. No entrena ni selecciona modelos.
    """
    import pandas as pd
    from mlflow.models import infer_signature

    if mlflow.active_run() is None:
        raise RuntimeError("Se necesita un run activo para guardar los artefactos.")
    if not isinstance(input_example, pd.DataFrame) or not 1 <= len(input_example) <= 5:
        raise ValueError("input_example debe ser un DataFrame de una a cinco filas agregadas.")
    forbidden = {"user_id", "usuario", "usuario_id", "id_usuario", "trip_id", "viaje",
                 "email", "correo", "nombre", "name", "birth_date", "fecha_nacimiento"}
    if forbidden.intersection(str(c).strip().lower() for c in input_example.columns):
        raise ValueError("El ejemplo contiene campos personales o identificadores de viajes.")
    if flavor not in {"sklearn", "pyfunc"}:
        raise ValueError("flavor debe ser sklearn o pyfunc.")
    paths = list(manifest_paths if manifest_paths is not None else [
        C.REFERENCES / "data_manifest.json", C.REFERENCES / "split_manifest.json"])
    manifests = {}
    for path in paths:
        path = Path(path)
        manifests[path.name] = json.loads(path.read_text(encoding="utf-8"))
    if not {"data_manifest.json", "split_manifest.json"}.issubset(manifests):
        raise ValueError("Se requieren los manifiestos de datos y partición.")
    data_version = manifests["data_manifest.json"]["data_version"]
    split = manifests["split_manifest.json"]
    if split["data_version"] != data_version:
        raise ValueError("Los manifiestos corresponden a versiones distintas de datos.")
    # Solo metadatos y parámetros resueltos; no debe contener credenciales.
    def check_keys(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if any(s in str(key).lower() for s in ("password", "token", "secret", "credential")):
                    raise ValueError("La configuración contiene una clave sensible.")
                check_keys(item)
        elif isinstance(value, (list, tuple)):
            for item in value:
                check_keys(item)
    check_keys(resolved_config)
    config_text = json.dumps(resolved_config, ensure_ascii=False, indent=2, allow_nan=False)
    plots = [Path(p) for p in plots]
    if any(not p.is_file() for p in plots):
        raise FileNotFoundError("Falta una de las gráficas solicitadas.")
    predictions = (model.predict(input_example) if flavor == "sklearn"
                   else model.predict(None, input_example))
    signature = infer_signature(input_example, predictions)
    requirements = [line.strip() for line in (C.ROOT / "requirements.txt").read_text().splitlines()
                    if line.strip() and not line.lstrip().startswith("#")]
    # Empaqueta el módulo para cargar clases propias sin depender del clon original.
    kwargs = dict(artifact_path="model", signature=signature,
                  input_example=input_example, pip_requirements=requirements,
                  code_paths=[str(C.ROOT / "mibici_equipo39")])
    if flavor == "sklearn":
        info = mlflow.sklearn.log_model(sk_model=model, **kwargs)
    else:
        info = mlflow.pyfunc.log_model(python_model=model, **kwargs)
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        config_file = folder / "resolved.json"
        config_file.write_text(config_text + "\n", encoding="utf-8")
        mlflow.log_artifact(str(config_file), "config")
        for name, payload in manifests.items():
            target = folder / name
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            mlflow.log_artifact(str(target), "data")
    if evaluation is not None:
        mlflow.log_dict(evaluation, "evaluation/summary.json")
    for plot in plots:
        mlflow.log_artifact(str(plot), "plots")
    mlflow.set_tags({"data_version": data_version, "split_id": split["split_id"],
                     "split_version": split["version"], "artifact_contract": "2"})
    return info.model_uri
