import argparse
import json
import os
from pathlib import Path

import mlflow
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, confusion_matrix
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from mibici_equipo39 import config as C
from mibici_equipo39 import plots
from mibici_equipo39.features import FEATURE_COLUMNS, load_p2_targets, load_tables, proxy_labels
from mibici_equipo39.modeling.stage2 import Fitted, QuestionAdapter
from mibici_equipo39.modeling.tracking import common_params, common_tags, log_model_run

TARGETS = {"bikes": "y_bikes", "docks": "y_docks"}
NUMERIC = list(FEATURE_COLUMNS)
CATEGORICAL = ["station_id"]
COLUMNS = NUMERIC + CATEGORICAL
FORBIDDEN = {"y_bikes", "y_docks", "flow_min", "flow_max", "capacity", "departures", "arrivals"}


def make_baseline():
    return DummyClassifier(strategy="prior")


def make_candidate():
    columns = ColumnTransformer(
        [
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=True), CATEGORICAL),
        ]
    )
    return make_pipeline(columns, LogisticRegression(**C.P2_LOGISTIC_PARAMS))


MODELS = {"baseline": make_baseline, "candidato": make_candidate}


def _scores(y, alert):
    tn, fp, fn, tp = confusion_matrix(y, alert, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}, precision, recall, f1


def threshold_search(y, score, grid=C.P2_THRESHOLDS):
    rows = [(t, *_scores(y, score >= t)[1:]) for t in grid]
    return pd.DataFrame(rows, columns=["threshold", "precision", "recall", "f1"])


def choose_threshold(y, score, grid=C.P2_THRESHOLDS, min_recall=C.P2_MIN_RECALL):
    """Mayor precisión con recall >= min_recall; si ninguno cumple, mayor F1. En empate, el umbral más alto."""
    table = threshold_search(y, score, grid)
    ok = table.loc[table["recall"].ge(min_recall)]
    pool, column, rule = (ok, "precision", "recall_floor") if len(ok) else (table, "f1", "max_f1")
    return float(pool.loc[pool[column].eq(pool[column].max()), "threshold"].max()), rule


def classification_metrics(y, score, threshold):
    confusion, precision, recall, f1 = _scores(y, score >= threshold)
    values = {
        "recall": recall,
        "precision": precision,
        "f1": f1,
        "support_positive": int(np.sum(y)),
    }
    if values["support_positive"]:
        values["ap"] = average_precision_score(y, score)
    return values, confusion


class P2Experiment:
    """DummyClassifier(prior) contra regresión logística, un modelo independiente por riesgo."""

    def __init__(self, metadata, X, targets):
        if FORBIDDEN & set(COLUMNS):
            raise ValueError("X incluye etiquetas, flujo de la hora objetivo o capacidad.")
        frame = pd.concat([metadata, X, targets], axis=1)
        self.frame = frame.loc[frame["capacity"].notna()].reset_index(drop=True)
        self.frame[list(TARGETS.values())] = self.frame[list(TARGETS.values())].astype(int)
        self.split = self.frame["split"]

    def _fit_target(self, factory, target):
        train = self.frame.loc[self.split.eq("train")]
        model = factory() if train[target].nunique() > 1 else make_baseline()
        model.fit(train[COLUMNS], train[target])
        positive = np.flatnonzero(model.classes_ == 1)
        score = (
            model.predict_proba(self.frame[COLUMNS])[:, positive[0]]
            if len(positive)
            else np.zeros(len(self.frame), dtype=float)
        )
        fitted_model = type(model.steps[-1][1]).__name__ if hasattr(model, "steps") else type(model).__name__
        y = self.frame[target].to_numpy()
        val = self.split.eq("validation").to_numpy()
        threshold, rule = choose_threshold(y[val], score[val])
        metrics, confusions = {}, {}
        for prefix, split in [("val", "validation"), ("test", "test")]:
            mask = self.split.eq(split).to_numpy()
            metrics[prefix], confusions[prefix] = classification_metrics(
                y[mask], score[mask], threshold
            )
        return (
            score,
            {"threshold": threshold, "rule": rule},
            metrics,
            confusions,
            threshold_search(y[val], score[val]),
            fitted_model,
        )

    def fit(self):
        self.scores, self.thresholds, self.metrics, self.confusions, self.searches = (
            {},
            {},
            {},
            {},
            {},
        )
        self.actual_models = {}
        for kind, factory in MODELS.items():
            results = {name: self._fit_target(factory, target) for name, target in TARGETS.items()}
            self.scores[kind] = {name: r[0] for name, r in results.items()}
            self.thresholds[kind] = {name: r[1] for name, r in results.items()}
            self.searches[kind] = {name: r[4] for name, r in results.items()}
            self.actual_models[kind] = {name: r[5] for name, r in results.items()}
            self.confusions[kind] = {
                f"{p}_{name}": r[3][p] for name, r in results.items() for p in ("val", "test")
            }
            metrics = {
                f"{p}_{k}_{name}": v
                for name, r in results.items()
                for p in ("val", "test")
                for k, v in r[2][p].items()
            }
            for p in ("val", "test"):
                metrics[f"{p}_macro_f1"] = (
                    metrics[f"{p}_f1_bikes"] + metrics[f"{p}_f1_docks"]
                ) / 2
            self.metrics[kind] = metrics
        better = (
            self.metrics["candidato"]["val_macro_f1"] > self.metrics["baseline"]["val_macro_f1"]
        )
        self.selected = "candidato" if better else "baseline"
        return self

    def prevalence(self):
        return {
            f"{split}_prevalence_{name}": float(
                self.frame.loc[self.split.eq(split), target].mean()
            )
            for split in ("train", "validation", "test")
            for name, target in TARGETS.items()
        }

    def sensitivity(self):
        """Cuántas etiquetas cambian si la ocupación inicial es 25% o 75% en lugar de 50%."""
        out = {}
        for occupancy in C.P2_SENSITIVITY_OCCUPANCIES:
            bikes, docks = proxy_labels(
                self.frame["flow_min"],
                self.frame["flow_max"],
                self.frame["capacity"],
                occupancy=occupancy,
            )
            out[str(occupancy)] = {
                "prevalence_bikes": float(bikes.mean()),
                "prevalence_docks": float(docks.mean()),
                "changed_bikes": float((bikes != self.frame["y_bikes"]).mean()),
                "changed_docks": float((docks != self.frame["y_docks"]).mean()),
            }
        return out

    def log(self, executor):
        models = {
            "baseline": (
                "P2-baseline-dummy-prior",
                {"model": "DummyClassifier", "strategy": "prior"},
            ),
            "candidato": (
                "P2-candidato-logistica",
                {
                    "model": "LogisticRegression",
                    "numeric": ",".join(NUMERIC),
                    "categorical": ",".join(CATEGORICAL),
                    "numeric_steps": "SimpleImputer(median)+StandardScaler",
                    "categorical_steps": "OneHotEncoder(ignore,sparse)",
                    **C.P2_LOGISTIC_PARAMS,
                },
            ),
        }
        params = {
            **common_params(self.frame),
            "capacity_source": Path(C.STATIONS_URL).name,
            "initial_occupancy": C.P2_INITIAL_OCCUPANCY,
            "margin": C.P2_MARGIN,
            "min_recall": C.P2_MIN_RECALL,
            "threshold_grid": "0.05-0.95 step 0.05",
            "selected_model": self.selected,
        }
        tags = common_tags(
            "P2",
            "classification",
            executor,
            "persona3",
            "riesgo_proxy_bicicletas y riesgo_proxy_anclajes",
        )
        prevalence, sensitivity = self.prevalence(), json.dumps(self.sensitivity(), indent=2)
        C.FIGURES.mkdir(parents=True, exist_ok=True)
        figure = plots.p2_precision_recall(
            self.frame, self.scores, TARGETS, C.FIGURES / "p2_precision_recall.png"
        )
        notes = (
            f"Seleccionado: {self.selected}. Candidato solo si mejora val_macro_f1.\n"
            f"Umbral por riesgo en validación: rejilla 0.05-0.95; mayor precisión con recall >= {C.P2_MIN_RECALL}, "
            "si no, mayor F1; empate al umbral más alto. Prueba sin reajustar.\n"
            "Etiqueta aproximada: no hay inventario observado.\n"
        )
        for kind, (run_name, extra) in models.items():
            thresholds = self.thresholds[kind]
            texts = {
                "metrics.json": json.dumps(
                    {**self.metrics[kind], **prevalence, "thresholds": thresholds}, indent=2
                ),
                "sensitivity.json": sensitivity,
                "evaluation_notes.txt": notes,
            }
            for name in TARGETS:
                texts[f"confusion_{name}.json"] = json.dumps(
                    {k: v for k, v in self.confusions[kind].items() if k.endswith(name)}, indent=2
                )
                texts[f"threshold_search_{name}.csv"] = self.searches[kind][name].to_csv(
                    index=False
                )
            run_params = {
                **params,
                **extra,
                **{f"threshold_{n}": t["threshold"] for n, t in thresholds.items()},
                **{f"threshold_rule_{n}": t["rule"] for n, t in thresholds.items()},
                **{f"actual_model_{n}": model for n, model in self.actual_models[kind].items()},
            }
            run_tags = {**tags, "model_role": kind, "selected": str(kind == self.selected).lower()}
            log_model_run(
                run_name,
                run_tags,
                run_params,
                {**self.metrics[kind], **prevalence},
                texts,
                [figure],
            )


def positive_proba(model, X):
    """Probabilidad de la clase 1; ceros si train solo tuvo una clase."""
    positive = np.flatnonzero(model.classes_ == 1)
    if not len(positive):
        return np.zeros(len(X), dtype=float)
    return model.predict_proba(X)[:, positive[0]]


def occupancy_sensitivity(frame, output, occupancies=C.P2_SENSITIVITY_OCCUPANCIES):
    """Etiquetas con otra ocupación inicial contra las alertas ya congeladas; no cambia la etiqueta principal."""
    out = {}
    for occupancy in occupancies:
        labels = dict(zip(TARGETS, proxy_labels(frame["flow_min"], frame["flow_max"], frame["capacity"],
                                                occupancy=occupancy)))
        out[str(occupancy)] = {}
        for risk, target in TARGETS.items():
            y = labels[risk].to_numpy()
            _, precision, recall, _ = _scores(y, output[f"alert_{risk}"].to_numpy())
            out[str(occupancy)][risk] = {
                "prevalence": float(y.mean()),
                "changed_vs_main": float((y != frame[target].to_numpy()).mean()),
                "support_positive": int(y.sum()),
                "recall": float(recall) if y.sum() else None,
                "precision": float(precision) if output[f"alert_{risk}"].any() else None,
            }
    return out


class P2RiskModel(mlflow.pyfunc.PythonModel):
    """Modelo de P2 para MLflow: dos clasificadores con sus umbrales congelados.

    predict devuelve prob_bikes, prob_docks, alert_bikes y alert_docks, una fila por entrada.
    Si ambas alertas se activan la estación oscila y requiere revisión; no indica que esté
    vacía y llena a la vez.
    """

    def __init__(self, pipelines, thresholds):
        self.pipelines = pipelines
        self.thresholds = thresholds

    def predict(self, context, model_input: pd.DataFrame, params=None) -> pd.DataFrame:
        if set(self.thresholds) != set(TARGETS):
            raise ValueError("El modelo no tiene umbrales para ambos riesgos; falta calibrate.")
        missing = set(COLUMNS) - set(model_input.columns)
        if missing:
            raise ValueError(f"Faltan columnas de entrada: {', '.join(sorted(missing))}.")
        X = model_input[COLUMNS]
        if X.empty:
            probs = {risk: np.zeros(0, dtype=float) for risk in TARGETS}
        else:
            probs = {risk: positive_proba(self.pipelines[risk], X) for risk in TARGETS}
        return pd.DataFrame(
            {**{f"prob_{r}": p for r, p in probs.items()},
             **{f"alert_{r}": p >= self.thresholds[r] for r, p in probs.items()}},
            index=model_input.index,
        )


class P2Adapter(QuestionAdapter):
    """Conecta P2 con el controlador de la etapa 2."""

    question, selection_metric, greater_is_better = "p2", "val_macro_f1", True
    needs_calibration = True

    def baseline(self):
        return {"name": "baseline", "family": "dummy", "params": {"strategy": "prior"}}

    def load_data(self):
        metadata, X, _ = load_tables()
        frame = pd.concat([metadata, X, load_p2_targets()], axis=1)
        frame = frame.loc[frame["capacity"].notna()].reset_index(drop=True)
        frame[list(TARGETS.values())] = frame[list(TARGETS.values())].astype(int)
        return frame

    def _estimator(self, variant):
        if variant["family"] == "dummy":
            return DummyClassifier(**variant["params"])
        if variant["family"] == "logistic":
            params = {f"logisticregression__{k}": v for k, v in variant["params"].items()}
            return make_candidate().set_params(**params)
        raise ValueError(f"Familia de P2 desconocida: {variant['family']}")

    def fit(self, variant, data):
        """Ajusta las dos cabezas solo con train; los umbrales se fijan después en calibrate."""
        train = data.loc[data["split"].eq("train")]
        pipelines = {}
        for risk, target in TARGETS.items():
            model = self._estimator(variant) if train[target].nunique() > 1 else make_baseline()
            pipelines[risk] = model.fit(train[COLUMNS], train[target])
        config = {"threshold_grid": list(C.P2_THRESHOLDS), "min_recall": C.P2_MIN_RECALL,
                  "initial_occupancy": C.P2_INITIAL_OCCUPANCY, "margin": C.P2_MARGIN,
                  "input_columns": COLUMNS, "excluded_columns": sorted(FORBIDDEN)}
        return Fitted(variant, P2RiskModel(pipelines, {}), "pyfunc", extra={"config": config})

    def calibrate(self, fitted, data, frozen=None):
        """Umbral por riesgo elegido con validation o, en una reproducción, el congelado en selection.json.

        La tabla de búsqueda en validation se calcula en ambos casos para las gráficas.
        """
        val = data.loc[data["split"].eq("validation")]
        if frozen is not None and set(frozen.get("thresholds", {})) != set(TARGETS):
            raise ValueError("La calibración congelada de P2 debe traer umbrales de bikes y docks.")
        thresholds, rules, searches = {}, {}, {}
        for risk, target in TARGETS.items():
            y, score = val[target].to_numpy(), positive_proba(fitted.model.pipelines[risk], val[COLUMNS])
            searches[risk] = threshold_search(y, score).to_dict(orient="records")
            if frozen is None:
                thresholds[risk], rules[risk] = choose_threshold(y, score)
            else:
                thresholds[risk], rules[risk] = float(frozen["thresholds"][risk]), "selection"
        fitted.model.thresholds = thresholds
        fitted.extra["config"].update(thresholds=thresholds, threshold_rules=rules)
        fitted.extra["evaluation"] = {"threshold_search_validation": searches}
        return {"thresholds": thresholds}

    def evaluate(self, fitted, data, split):
        """Métricas por riesgo; las que no se pueden calcular se omiten y su causa queda en evaluation."""
        prefix = {"train": "train", "validation": "val", "test": "test"}[split]
        frame = data.loc[data["split"].eq(split)]
        output = fitted.model.predict(None, frame[COLUMNS])
        evaluation = fitted.extra.setdefault("evaluation", {})
        not_evaluable = evaluation.setdefault("not_evaluable", {})
        metrics = {}
        for risk, target in TARGETS.items():
            y = frame[target].to_numpy()
            values, _ = classification_metrics(y, output[f"prob_{risk}"].to_numpy(), fitted.model.thresholds[risk])
            if not values["support_positive"]:
                for name in ("recall", "f1"):
                    values.pop(name)
                    not_evaluable[f"{prefix}_{name}_{risk}"] = f"sin positivos de {risk} en {split}"
                not_evaluable[f"{prefix}_ap_{risk}"] = f"sin positivos de {risk} en {split}"
            if not output[f"alert_{risk}"].any():
                values.pop("precision")
                not_evaluable[f"{prefix}_precision_{risk}"] = f"el modelo no emite alertas de {risk} en {split}"
            metrics.update({f"{prefix}_{k}_{risk}": v for k, v in values.items()})
            metrics[f"{prefix}_prevalence_{risk}"] = float(y.mean())
            metrics[f"{prefix}_alerts_per_1000_{risk}"] = 1000 * float(output[f"alert_{risk}"].mean())
        f1 = [metrics.get(f"{prefix}_f1_{risk}") for risk in TARGETS]
        if None in f1:
            not_evaluable[f"{prefix}_macro_f1"] = "falta el F1 de algún riesgo"
        else:
            metrics[f"{prefix}_macro_f1"] = sum(f1) / len(f1)
        if split in ("validation", "test"):
            evaluation.setdefault("initial_occupancy_sensitivity", {})[split] = occupancy_sensitivity(
                frame, output)
        return metrics

    def input_example(self, fitted, data):
        example = data.loc[data["split"].eq("validation"), COLUMNS].head(3).reset_index(drop=True)
        example[NUMERIC] = example[NUMERIC].astype(float)
        example["station_id"] = example["station_id"].astype(str)
        return example

    def plots(self, fitted, data, folder):
        frame = data.loc[data["split"].eq("validation")]
        output = fitted.model.predict(None, frame[COLUMNS])
        searches = fitted.extra["evaluation"]["threshold_search_validation"]
        return [
            plots.p2_confusion_matrices(frame, output, fitted.model.thresholds, folder / "p2_matrices_confusion_validacion.png"),
            plots.p2_risk_pr_curves(frame, output, folder / "p2_precision_recall_validacion.png", C.P2_MIN_RECALL),
            plots.p2_threshold_curves(searches, fitted.model.thresholds, folder / "p2_umbrales_validacion.png", C.P2_MIN_RECALL),
        ]


ADAPTER = P2Adapter()


def main():
    parser = argparse.ArgumentParser(
        description="P2: riesgo aproximado de falta de bicicletas o anclajes"
    )
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "local"))
    metadata, X, _ = load_tables()
    experiment = P2Experiment(metadata, X, load_p2_targets()).fit()
    experiment.log(parser.parse_args().executor)
    print(
        json.dumps(
            {
                "selected": experiment.selected,
                "thresholds": experiment.thresholds,
                **experiment.metrics,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
