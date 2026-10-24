"""Controlador de la etapa 2: búsqueda anidada por pregunta y reproducción de la selección.

Se ejecuta con `mlflow run . -e train -P question=p1|p2|p3`. Cada pregunta expone un
ADAPTER en su módulo; este archivo no entrena por sí mismo.
"""

from abc import ABC, abstractmethod
import argparse
import copy
from dataclasses import dataclass, field
from importlib import import_module
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

import mlflow
import numpy as np
import pandas as pd

from mibici_equipo39 import config as C
from mibici_equipo39.modeling import tracking

DELIVERY = "A6"
MEMBERS = ("Marco", "Stefania", "DiegoMartinez", "DiegoHurtado")
CODE_AUTHORS = {"p1": "Stefania", "p2": "DiegoMartinez", "p3": "DiegoHurtado"}
SPLITS = (("train", "train"), ("validation", "val"), ("test", "test"))


@dataclass
class Fitted:
    """extra["config"] se agrega a config/resolved.json y extra["evaluation"] a evaluation/summary.json."""

    variant: dict
    model: object
    flavor: str
    extra: dict = field(default_factory=dict)


class QuestionAdapter(ABC):
    """Lo que cada pregunta expone como ADAPTER para que el controlador la entrene."""

    question: str
    selection_metric: str
    greater_is_better: bool

    @abstractmethod
    def baseline(self) -> dict:
        """Variante baseline con name, family y params."""

    @abstractmethod
    def load_data(self):
        """Tablas construidas por features.py, con la partición confirmada."""

    @abstractmethod
    def fit(self, variant, data) -> Fitted:
        """Ajusta la variante solo con train."""

    @abstractmethod
    def evaluate(self, fitted, data, split) -> dict:
        """Métricas de split ('train', 'validation' o 'test') con prefijo train_, val_ o test_."""

    @abstractmethod
    def input_example(self, fitted, data):
        """DataFrame de 1 a 5 filas agregadas para la firma, sin datos personales."""

    @abstractmethod
    def plots(self, fitted, data, folder) -> list:
        """Rutas de las gráficas propias de la pregunta guardadas en folder."""

    def eligible(self, val_metrics) -> bool:
        """Si la variante puede ganar; P3 la usa para exigir grupos válidos."""
        return True


ADAPTERS = {
    "p1": "mibici_equipo39.modeling.p1",
    "p2": "mibici_equipo39.modeling.p2",
    "p3": "mibici_equipo39.modeling.p3",
}


def load_adapter(question):
    if question not in ADAPTERS:
        raise ValueError(f"Pregunta desconocida: {question}. Usa p1, p2 o p3.")
    adapter = getattr(import_module(ADAPTERS[question]), "ADAPTER", None)
    if adapter is None:
        raise RuntimeError(f"{question} todavía no expone ADAPTER; lo agrega su responsable en su PR.")
    if not isinstance(adapter, QuestionAdapter):
        raise TypeError(f"El ADAPTER de {question} no hereda de QuestionAdapter.")
    return adapter


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Búsqueda y reproducción de la etapa 2")
    parser.add_argument("--question", required=True, choices=list(ADAPTERS))
    parser.add_argument("--model", default="search", choices=["search", "selected"])
    parser.add_argument("--hyperparameters", default="config")
    parser.add_argument("--member", default="config")
    parser.add_argument("--mode", default="search", choices=["search", "reproduce"])
    parser.add_argument("--allow-dirty", action="store_true", help="Solo para depurar; la corrida queda como development.")
    args = parser.parse_args(argv)
    if (args.model == "selected") != (args.mode == "reproduce"):
        parser.error("model=selected va con mode=reproduce, y model=search con mode=search.")
    return args


def resolve_member(member):
    if member == "config":
        member = os.environ.get("MIBICI_EXECUTOR", "")
    if member not in MEMBERS:
        raise ValueError(f"member debe ser uno de {', '.join(MEMBERS)} (o definir MIBICI_EXECUTOR).")
    return member


def load_overrides(source):
    if source == "config":
        return {}
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo de hiperparámetros: {source}")
    overrides = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(overrides, dict) or not all(isinstance(v, dict) for v in overrides.values()):
        raise ValueError('El JSON debe tener la forma {"variante": {"parametro": valor}}.')
    return overrides


def etapa2_path(name):
    return C.REFERENCES / "etapa2" / name


def read_selection(question):
    path = etapa2_path("selection.json")
    if not path.is_file():
        raise FileNotFoundError("Falta references/etapa2/selection.json; se publica después de la búsqueda oficial.")
    selection = json.loads(path.read_text(encoding="utf-8")).get(question)
    if not selection:
        raise ValueError(f"selection.json no tiene una selección para {question}.")
    return selection


def resolve_variants(adapter, model, overrides):
    if model == "selected":
        if overrides:
            raise ValueError("Una reproducción usa los hiperparámetros congelados; no acepta sobreescrituras.")
        chosen = read_selection(adapter.question)
        return [{"name": chosen["variant"], "family": chosen["family"], "params": dict(chosen["params"])}]
    variants = [adapter.baseline(), *copy.deepcopy(C.STAGE2_SEARCH_PLAN[adapter.question])]
    by_name = {v["name"]: v for v in variants}
    for name, params in overrides.items():
        if name not in by_name:
            raise ValueError(f"Variante desconocida en hiperparámetros: {name}. Opciones: {', '.join(by_name)}.")
        unknown = set(params) - set(by_name[name]["params"])
        if unknown:
            raise ValueError(f"Hiperparámetros desconocidos para {name}: {', '.join(sorted(unknown))}.")
        by_name[name]["params"].update(params)
    return variants


def resolve_config(args, member, variants):
    data = json.loads((C.REFERENCES / "data_manifest.json").read_text(encoding="utf-8"))
    split = json.loads((C.REFERENCES / "split_manifest.json").read_text(encoding="utf-8"))
    return {
        "delivery": DELIVERY,
        "question": args.question,
        "model": args.model,
        "mode": args.mode,
        "hyperparameters_source": args.hyperparameters,
        "member": member,
        "experiment": C.EXPERIMENT_NAME,
        "seed": C.SEED,
        "data_version": data["data_version"],
        "split_id": split["split_id"],
        "split_version": split["version"],
        "split_strategy": split["strategy"],
        "feature_schema_version": C.FEATURE_SCHEMA_VERSION,
        "variants": variants,
    }


def predict(fitted, example):
    if fitted.flavor == "pyfunc":
        return fitted.model.predict(None, example)
    return fitted.model.predict(example)


def to_jsonable(prediction):
    if isinstance(prediction, pd.DataFrame):
        return {"kind": "frame", "columns": list(prediction.columns),
                "data": json.loads(prediction.to_json(orient="values"))}
    return {"kind": "array", "data": np.asarray(prediction).tolist()}


def select(adapter, val_metrics):
    """Mejor métrica de validación entre las elegibles; el baseline gana un empate a 6 decimales."""
    metric, sign = adapter.selection_metric, 1 if adapter.greater_is_better else -1
    eligible = {name: m for name, m in val_metrics.items() if adapter.eligible(m) and metric in m}
    if not eligible:
        return None, f"ninguna variante es elegible por {metric}"
    best = max(round(sign * m[metric], 6) for m in eligible.values())
    tied = [name for name, m in eligible.items() if round(sign * m[metric], 6) == best]
    baseline = adapter.baseline()["name"]
    chosen = baseline if baseline in tied else tied[0]
    goal = "mayor" if adapter.greater_is_better else "menor"
    return chosen, f"{goal} {metric} entre elegibles; empate a 6 decimales lo gana el baseline"


def baseline_source_run_id(question):
    path = etapa2_path("starting_point.json")
    if not path.is_file():
        return None
    models = json.loads(path.read_text(encoding="utf-8")).get("models", [])
    for entry in models:
        if entry.get("question", "").lower() == question and entry.get("role") == "baseline":
            return entry.get("run_id")
    return None


def log_child(adapter, data, fitted, metrics, tags, config, experiment_id):
    """Una corrida hija por variante con métricas, artefactos y predicción de ejemplo."""
    variant = fitted.variant
    name = f"{DELIVERY}-{adapter.question}-{variant['name']}-{config['member']}"
    with mlflow.start_run(run_name=name, nested=True, experiment_id=experiment_id) as run:
        mlflow.set_tags({**tags, "model_family": variant["family"], "variant_id": variant["name"]})
        mlflow.log_params({"variant_id": variant["name"], "model_family": variant["family"],
                           **{f"hp_{k}": v for k, v in variant["params"].items()},
                           **{k: config[k] for k in ("seed", "data_version", "split_version", "feature_schema_version")}})
        mlflow.log_metrics(metrics)
        example = adapter.input_example(fitted, data)
        prediction = to_jsonable(predict(fitted, example))
        resolved = {**{k: v for k, v in config.items() if k != "variants"}, "variant": variant,
                    **fitted.extra.get("config", {})}
        evaluation = {"metrics": metrics, "selection_metric": adapter.selection_metric,
                      **fitted.extra.get("evaluation", {})}
        with tempfile.TemporaryDirectory() as tmp:
            plots = adapter.plots(fitted, data, Path(tmp))
            tracking.log_candidate_artifacts(
                fitted.model, example, resolved, flavor=fitted.flavor, plots=plots, evaluation=evaluation,
            )
        mlflow.log_dict(prediction, "evaluation/example_prediction.json")
        return run.info.run_id


def fit_all(adapter, data, variants):
    fitted, val_metrics, seconds = {}, {}, {}
    for variant in variants:
        start = time.perf_counter()
        fitted[variant["name"]] = adapter.fit(variant, data)
        seconds[variant["name"]] = time.perf_counter() - start
        val_metrics[variant["name"]] = adapter.evaluate(fitted[variant["name"]], data, "validation")
    return fitted, val_metrics, seconds


def all_metrics(adapter, fitted, data, val_metrics, fit_seconds):
    metrics = {**adapter.evaluate(fitted, data, "train"), **val_metrics,
               **adapter.evaluate(fitted, data, "test"), "fit_seconds": fit_seconds}
    return {k: float(v) for k, v in metrics.items() if v is not None}


def run_search(adapter, data, config, base_tags, experiment_id):
    fitted, val_metrics, seconds = fit_all(adapter, data, config["variants"])
    chosen, rule = select(adapter, val_metrics)
    # La elección queda escrita antes de calcular cualquier métrica de prueba.
    mlflow.log_dict({"selected_variant": chosen, "rule": rule, "validation_metrics": val_metrics},
                    "evaluation/selection_before_test.json")
    baseline = adapter.baseline()["name"]
    run_ids = {}
    for name, model in fitted.items():
        tags = {**base_tags, "stage_of_work": "baseline" if name == baseline else "candidate",
                "selected": str(name == chosen).lower()}
        if name == baseline and (source := baseline_source_run_id(adapter.question)):
            tags["baseline_source_run_id"] = source
        metrics = all_metrics(adapter, model, data, val_metrics[name], seconds[name])
        run_ids[name] = log_child(adapter, data, model, metrics, tags, config, experiment_id)
    mlflow.set_tags({"selected_variant": str(chosen), "selected_run_id": run_ids.get(chosen, "")})
    return chosen, run_ids


def run_reproduce(adapter, data, config, base_tags, experiment_id):
    selection = read_selection(adapter.question)
    fitted, val_metrics, seconds = fit_all(adapter, data, config["variants"])
    name = config["variants"][0]["name"]
    metrics = all_metrics(adapter, fitted[name], data, val_metrics[name], seconds[name])
    tags = {**base_tags, "stage_of_work": "reproduce", "reproduces_run_id": selection.get("run_id", "")}
    run_id = log_child(adapter, data, fitted[name], metrics, tags, config, experiment_id)
    mlflow.set_tags({"selected_variant": name, "selected_run_id": run_id})
    return name, {name: run_id}


def main(argv=None):
    args = parse_args(argv)
    member = resolve_member(args.member)
    adapter = load_adapter(args.question)
    variants = resolve_variants(adapter, args.model, load_overrides(args.hyperparameters))
    config = resolve_config(args, member, variants)
    print(json.dumps(config, ensure_ascii=False, indent=2))

    # mlflow run crea el padre y lo pasa en MLFLOW_RUN_ID; si queda en el entorno, cada
    # start_run reabriría al padre en lugar de crear hijas.
    project_run_id = os.environ.pop("MLFLOW_RUN_ID", None)
    if not project_run_id:
        raise RuntimeError("Ejecuta el entrenamiento con mlflow run (falta MLFLOW_RUN_ID).")
    commit, dirty = tracking.git_state()
    if dirty and not args.allow_dirty:
        raise RuntimeError("Hay cambios sin commit; las corridas deben quedar ligadas a un commit.")

    mlflow.set_tracking_uri(C.TRACKING_URI)
    mlflow.set_registry_uri(C.REGISTRY_URI)
    parent = mlflow.MlflowClient().get_run(project_run_id)
    experiment = mlflow.get_experiment(parent.info.experiment_id)
    if experiment.name != C.EXPERIMENT_NAME:
        raise RuntimeError(f"El padre está en {experiment.name}; usa --experiment-name {C.EXPERIMENT_NAME}.")
    mlflow.set_experiment(experiment_id=experiment.experiment_id)

    search_id = project_run_id if args.mode == "search" else f"reproduce-{uuid.uuid4().hex[:8]}"
    base_tags = {"team": C.TEAM, "question": args.question, "delivery": DELIVERY,
                 "executor": member, "code_author": CODE_AUTHORS[args.question],
                 "git_commit": commit, "git_dirty": str(dirty).lower(), "search_id": search_id,
                 "data_version": config["data_version"], "split_version": config["split_version"]}
    if dirty:
        base_tags["development"] = "true"

    data = adapter.load_data()
    with mlflow.start_run(run_id=project_run_id):
        mlflow.set_tags({**base_tags, "stage_of_work": "search" if args.mode == "search" else "reproduce"})
        mlflow.log_dict(config, "config/resolved_search.json")
        runner = run_search if args.mode == "search" else run_reproduce
        chosen, run_ids = runner(adapter, data, config, base_tags, parent.info.experiment_id)

    summary = {"question": args.question, "mode": args.mode, "selected_variant": chosen,
               "parent_run_id": project_run_id, "child_run_ids": run_ids, "git_commit": commit}
    out = C.RESULTS_DIR / "stage2" / f"{args.question}_{args.mode}_{project_run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    # Con python -m este archivo corre como __main__; se usa el módulo del paquete para que
    # QuestionAdapter sea la misma clase de la que heredan los adaptadores.
    import_module("mibici_equipo39.modeling.stage2").main()
