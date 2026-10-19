import argparse
import json
import os
from pathlib import Path
import tempfile

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
from mibici_equipo39.modeling.tracking import common_params, common_tags, question_run

TARGETS = {"bikes": "y_bikes", "docks": "y_docks"}
NUMERIC = list(FEATURE_COLUMNS)
CATEGORICAL = ["station_id"]
FORBIDDEN = {"y_bikes", "y_docks", "flow_min", "flow_max", "capacity", "departures", "arrivals"}


def make_baseline():
    return DummyClassifier(strategy="prior")


def make_candidate():
    columns = ColumnTransformer([
        ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
        ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=True), CATEGORICAL),
    ])
    return make_pipeline(columns, LogisticRegression(**C.P2_LOGISTIC_PARAMS))


def _counts(y, alert):
    tn, fp, fn, tp = confusion_matrix(y, alert, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}, precision, recall, f1


def threshold_search(y, score, grid=C.P2_THRESHOLDS):
    rows = []
    for threshold in grid:
        _, precision, recall, f1 = _counts(y, score >= threshold)
        rows.append({"threshold": threshold, "precision": precision, "recall": recall, "f1": f1})
    return pd.DataFrame(rows)


def choose_threshold(y, score, grid=C.P2_THRESHOLDS, min_recall=C.P2_MIN_RECALL):
    """Mayor precisión con recall >= min_recall; si ninguno cumple, mayor F1. En empate, el umbral más alto."""
    table = threshold_search(y, score, grid)
    ok = table.loc[table["recall"].ge(min_recall)]
    pool, column, rule = (ok, "precision", "recall_floor") if len(ok) else (table, "f1", "max_f1")
    return float(pool.loc[pool[column].eq(pool[column].max()), "threshold"].max()), rule


def classification_metrics(y, score, threshold):
    confusion, precision, recall, f1 = _counts(y, score >= threshold)
    values = {"recall": recall, "precision": precision, "f1": f1, "support_positive": int(np.sum(y))}
    if values["support_positive"]:
        values["ap"] = average_precision_score(y, score)
    return values, confusion


class P2Experiment:
    """DummyClassifier(prior) contra regresión logística, un modelo independiente por riesgo."""

    def __init__(self, metadata, X, targets):
        if FORBIDDEN & set(NUMERIC + CATEGORICAL):
            raise ValueError("X incluye etiquetas, flujo de la hora objetivo o capacidad.")
        frame = pd.concat([metadata, X, targets], axis=1)
        self.frame = frame.loc[frame["capacity"].notna()].reset_index(drop=True)
        for target in TARGETS.values():
            self.frame[target] = self.frame[target].astype(int)
        self.split = self.frame["split"]

    def fit(self):
        train = self.frame.loc[self.split.eq("train")]
        X_all = self.frame[NUMERIC + CATEGORICAL]
        self.scores, self.thresholds, self.metrics, self.confusions, self.searches = {}, {}, {}, {}, {}
        for kind, factory in [("baseline", make_baseline), ("candidato", make_candidate)]:
            metrics, confusions, thresholds, scores, searches = {}, {}, {}, {}, {}
            for name, target in TARGETS.items():
                y_train = train[target]
                model = factory() if y_train.nunique() > 1 else make_baseline()
                score = model.fit(train[NUMERIC + CATEGORICAL], y_train).predict_proba(X_all)[:, 1]
                y = self.frame[target].to_numpy()
                val = self.split.eq("validation").to_numpy()
                threshold, rule = choose_threshold(y[val], score[val])
                thresholds[name] = {"threshold": threshold, "rule": rule}
                searches[name] = threshold_search(y[val], score[val])
                for prefix, split in [("val", "validation"), ("test", "test")]:
                    mask = self.split.eq(split).to_numpy()
                    values, confusion = classification_metrics(y[mask], score[mask], threshold)
                    metrics.update({f"{prefix}_{k}_{name}": v for k, v in values.items()})
                    confusions[f"{prefix}_{name}"] = confusion
                scores[name] = score
            for prefix in ["val", "test"]:
                metrics[f"{prefix}_macro_f1"] = (metrics[f"{prefix}_f1_bikes"] + metrics[f"{prefix}_f1_docks"]) / 2
            self.scores[kind], self.thresholds[kind], self.metrics[kind] = scores, thresholds, metrics
            self.confusions[kind], self.searches[kind] = confusions, searches
        self.selected = "candidato" if self.metrics["candidato"]["val_macro_f1"] > self.metrics["baseline"]["val_macro_f1"] else "baseline"
        return self

    def prevalence(self):
        return {f"{split}_prevalence_{name}": float(self.frame.loc[self.split.eq(split), target].mean())
                for split in ["train", "validation", "test"] for name, target in TARGETS.items()}

    def sensitivity(self):
        """Cuántas etiquetas cambian si la ocupación inicial es 25% o 75% en lugar de 50%."""
        out = {}
        for occupancy in C.P2_SENSITIVITY_OCCUPANCIES:
            bikes, docks = proxy_labels(self.frame["flow_min"], self.frame["flow_max"], self.frame["capacity"], occupancy=occupancy)
            out[str(occupancy)] = {
                "prevalence_bikes": float(bikes.mean()), "prevalence_docks": float(docks.mean()),
                "changed_bikes": float((bikes != self.frame["y_bikes"]).mean()),
                "changed_docks": float((docks != self.frame["y_docks"]).mean()),
            }
        return out

    def log(self, executor):
        runs = {
            "baseline": ("P2-baseline-dummy-prior", {"model": "DummyClassifier", "strategy": "prior"}),
            "candidato": ("P2-candidato-logistica", {
                "model": "LogisticRegression", "numeric": ",".join(NUMERIC), "categorical": ",".join(CATEGORICAL),
                "numeric_steps": "SimpleImputer(median)+StandardScaler", "categorical_steps": "OneHotEncoder(ignore,sparse)",
                **C.P2_LOGISTIC_PARAMS,
            }),
        }
        params = {
            **common_params(self.frame), "capacity_source": Path(C.STATIONS_URL).name,
            "initial_occupancy": C.P2_INITIAL_OCCUPANCY, "margin": C.P2_MARGIN, "min_recall": C.P2_MIN_RECALL,
            "threshold_grid": "0.05-0.95 step 0.05", "selected_model": self.selected,
        }
        tags = common_tags("P2", "classification", executor, "persona3", "riesgo_proxy_bicicletas y riesgo_proxy_anclajes")
        prevalence, sensitivity = self.prevalence(), self.sensitivity()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            figure = plots.p2_precision_recall(self.frame, self.scores, TARGETS, folder / "p2_precision_recall.png")
            (folder / "sensitivity.json").write_text(json.dumps(sensitivity, indent=2))
            for kind, (run_name, extra) in runs.items():
                for name in TARGETS:
                    confusion = {k: v for k, v in self.confusions[kind].items() if k.endswith(name)}
                    (folder / f"confusion_{name}.json").write_text(json.dumps(confusion, indent=2))
                    self.searches[kind][name].to_csv(folder / f"threshold_search_{name}.csv", index=False)
                (folder / "metrics.json").write_text(json.dumps({**self.metrics[kind], **prevalence, "thresholds": self.thresholds[kind]}, indent=2))
                (folder / "evaluation_notes.txt").write_text(
                    f"Seleccionado: {self.selected}. Candidato solo si mejora val_macro_f1.\n"
                    f"Umbral por riesgo en validación: rejilla 0.05-0.95; mayor precisión con recall >= {C.P2_MIN_RECALL}, "
                    "si no, mayor F1; empate al umbral más alto. Prueba sin reajustar.\n"
                    "Etiqueta aproximada: no hay inventario observado.\n"
                )
                with question_run(run_name):
                    mlflow.set_tags({**tags, "model_role": kind, "selected": str(kind == self.selected).lower()})
                    mlflow.log_params({
                        **params, **extra,
                        **{f"threshold_{n}": t["threshold"] for n, t in self.thresholds[kind].items()},
                        **{f"threshold_rule_{n}": t["rule"] for n, t in self.thresholds[kind].items()},
                    })
                    mlflow.log_metrics({**self.metrics[kind], **prevalence})
                    for file in ["metrics.json", "sensitivity.json", "confusion_bikes.json", "confusion_docks.json",
                                 "threshold_search_bikes.csv", "threshold_search_docks.csv", "evaluation_notes.txt"]:
                        mlflow.log_artifact(str(folder / file))
                    mlflow.log_artifact(str(figure), "figures")
            C.FIGURES.mkdir(parents=True, exist_ok=True)
            (C.FIGURES / figure.name).write_bytes(figure.read_bytes())


def main():
    parser = argparse.ArgumentParser(description="P2: riesgo aproximado de falta de bicicletas o anclajes")
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "local"))
    metadata, X, _ = load_tables()
    experiment = P2Experiment(metadata, X, load_p2_targets()).fit()
    experiment.log(parser.parse_args().executor)
    print(json.dumps({"selected": experiment.selected, "thresholds": experiment.thresholds, **experiment.metrics}, indent=2))


if __name__ == "__main__":
    main()
