import argparse
import json
import os
from pathlib import Path
import tempfile

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, confusion_matrix, precision_recall_curve
from sklearn.preprocessing import TargetEncoder

from mibici_equipo39 import config as C
from mibici_equipo39 import plots
from mibici_equipo39.features import FEATURE_COLUMNS, load_p2_targets, load_tables, proxy_labels
from mibici_equipo39.modeling.tracking import common_params, common_tags, question_run

TARGETS = {"bikes": "y_bikes", "docks": "y_docks"}
FORBIDDEN = {"y_bikes", "y_docks", "flow_min", "flow_max", "capacity"}
ENCODED = ["te_station", "te_station_hour"]


class SeasonalRateBaseline:
    """Frecuencia de train por estación, fin de semana y hora; si falta, estación; luego global."""

    levels = (["station_id", "is_weekend", "hour_of_day"], ["station_id"])

    def fit(self, frame, y):
        self.rates_ = [y.groupby([frame[k] for k in keys], observed=True).mean().rename("rate") for keys in self.levels]
        self.global_ = float(y.mean())
        return self

    def score(self, frame):
        out = pd.Series(np.nan, index=frame.index)
        for keys, rates in zip(self.levels, self.rates_):
            out = out.fillna(frame[keys].join(rates, on=keys)["rate"])
        return out.fillna(self.global_).to_numpy()


class TargetEncodedHGB:
    """HistGradientBoosting con calendario, rezagos y tasa histórica por estación y estación-hora."""

    def _keys(self, frame):
        station = frame["station_id"].astype(str)
        return pd.DataFrame({
            "te_station": station,
            "te_station_hour": station + "|" + frame["is_weekend"].astype(str) + "|" + frame["hour_of_day"].astype(str),
        })

    def fit(self, frame, y):
        self.encoder_ = TargetEncoder(target_type="binary", cv=5, shuffle=True, random_state=C.SEED)
        encoded = pd.DataFrame(self.encoder_.fit_transform(self._keys(frame), y), columns=ENCODED, index=frame.index)
        self.model_ = HistGradientBoostingClassifier(**C.P2_HGB_PARAMS).fit(pd.concat([frame[FEATURE_COLUMNS], encoded], axis=1), y)
        return self

    def score(self, frame):
        encoded = pd.DataFrame(self.encoder_.transform(self._keys(frame)), columns=ENCODED, index=frame.index)
        return self.model_.predict_proba(pd.concat([frame[FEATURE_COLUMNS], encoded], axis=1))[:, 1]


def choose_threshold(y, score, min_recall=C.P2_MIN_RECALL):
    """Mayor precisión con recall >= min_recall en validación; si no se alcanza, mayor F1."""
    precision, recall, thresholds = precision_recall_curve(y, score)
    table = pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1]})
    table["f1"] = (2 * table["precision"] * table["recall"] / (table["precision"] + table["recall"])).fillna(0)
    ok = table.loc[table["recall"].ge(min_recall)]
    pool, column = (ok, "precision") if len(ok) else (table, "f1")
    return float(pool.loc[pool[column].eq(pool[column].max()), "threshold"].max())


def classification_metrics(y, score, threshold):
    alert = score >= threshold
    tn, fp, fn, tp = confusion_matrix(y, alert, labels=[0, 1]).ravel()
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    values = {"recall": recall, "precision": precision, "f1": f1, "ap": average_precision_score(y, score), "alert_rate": float(alert.mean())}
    return values, {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)}


class P2Experiment:
    """Baseline de frecuencia contra HGB con target encoding, un modelo por riesgo."""

    def __init__(self, metadata, X, targets):
        if FORBIDDEN & set(FEATURE_COLUMNS):
            raise ValueError("Hay columnas de la etiqueta dentro de X.")
        frame = pd.concat([metadata, X, targets], axis=1)
        self.frame = frame.loc[frame["capacity"].notna()].reset_index(drop=True)
        for target in TARGETS.values():
            self.frame[target] = self.frame[target].astype(int)
        self.split = self.frame["split"]

    def fit(self):
        train = self.frame.loc[self.split.eq("train")]
        self.scores, self.thresholds, self.metrics, self.confusions = {}, {}, {}, {}
        for kind, model in [("baseline", SeasonalRateBaseline), ("candidato", TargetEncodedHGB)]:
            metrics, confusions, thresholds, scores = {}, {}, {}, {}
            for name, target in TARGETS.items():
                score = model().fit(train, train[target]).score(self.frame)
                y = self.frame[target].to_numpy()
                val = self.split.eq("validation").to_numpy()
                thresholds[name] = choose_threshold(y[val], score[val])
                for prefix, split in [("val", "validation"), ("test", "test")]:
                    mask = self.split.eq(split).to_numpy()
                    values, confusion = classification_metrics(y[mask], score[mask], thresholds[name])
                    metrics.update({f"{prefix}_{k}_{name}": v for k, v in values.items()})
                    confusions[f"{prefix}_{name}"] = confusion
                scores[name] = score
            for prefix in ["val", "test"]:
                metrics[f"{prefix}_macro_f1"] = (metrics[f"{prefix}_f1_bikes"] + metrics[f"{prefix}_f1_docks"]) / 2
            self.scores[kind], self.thresholds[kind], self.metrics[kind], self.confusions[kind] = scores, thresholds, metrics, confusions
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
            "baseline": ("P2-baseline-frecuencia-estacion-hora", {"model": "seasonal_rate_station_weekend_hour"}),
            "candidato": ("P2-candidato-hgb-target-encoding", {"model": "HistGradientBoostingClassifier+TargetEncoder", "features": ",".join(FEATURE_COLUMNS + ENCODED), **C.P2_HGB_PARAMS}),
        }
        params = {
            **common_params(self.frame), "capacity_source": Path(C.STATIONS_URL).name,
            "initial_occupancy": C.P2_INITIAL_OCCUPANCY, "margin": C.P2_MARGIN, "min_recall": C.P2_MIN_RECALL,
            "selected_model": self.selected,
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
                (folder / "metrics.json").write_text(json.dumps({**self.metrics[kind], **prevalence, "thresholds": self.thresholds[kind]}, indent=2))
                (folder / "evaluation_notes.txt").write_text(
                    f"Seleccionado: {self.selected}. Criterio: mayor val_macro_f1 con umbral de recall >= {C.P2_MIN_RECALL} en validación.\n"
                    "Etiqueta aproximada: no hay inventario observado.\n"
                )
                with question_run(run_name):
                    mlflow.set_tags({**tags, "model_role": kind, "selected": str(kind == self.selected).lower()})
                    mlflow.log_params({**params, **extra, **{f"threshold_{n}": t for n, t in self.thresholds[kind].items()}})
                    mlflow.log_metrics({**self.metrics[kind], **prevalence})
                    for file in ["metrics.json", "sensitivity.json", "confusion_bikes.json", "confusion_docks.json", "evaluation_notes.txt"]:
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
    print(json.dumps({"selected": experiment.selected, **experiment.metrics}, indent=2))


if __name__ == "__main__":
    main()
