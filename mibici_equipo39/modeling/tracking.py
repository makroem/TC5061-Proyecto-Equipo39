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
    if mlflow.get_experiment_by_name(C.EXPERIMENT_NAME) is None:
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
