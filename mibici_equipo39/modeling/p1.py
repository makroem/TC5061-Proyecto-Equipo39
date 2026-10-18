import argparse
import json
import os
from pathlib import Path
import tempfile

import mlflow
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from mibici_equipo39 import config as C
from mibici_equipo39 import plots
from mibici_equipo39.features import FEATURE_COLUMNS, eligible_stations, load_tables
from mibici_equipo39.modeling.tracking import common_params, common_tags, question_run

SPLITS = {"train": "train", "val": "validation", "test": "test"}


class SeasonalMeanBaseline:
    """Media de train por estación, día y hora; si falta, estación y hora; al final la global."""

    levels = (["station_id", "day_of_week", "hour_of_day"], ["station_id", "hour_of_day"])

    def fit(self, frame, y):
        self.means_ = [y.groupby([frame[k] for k in keys], observed=True).mean().rename("mean") for keys in self.levels]
        self.global_ = float(y.mean())
        return self

    def predict(self, frame):
        pred = pd.Series(np.nan, index=frame.index)
        for keys, means in zip(self.levels, self.means_):
            pred = pred.fillna(frame[keys].join(means, on=keys)["mean"])
        return pred.fillna(self.global_).to_numpy()


def make_candidate():
    return HistGradientBoostingRegressor(**C.P1_HGB_PARAMS)


def regression_metrics(y, pred, split):
    out = {}
    for prefix, name in SPLITS.items():
        mask = split.eq(name).to_numpy()
        out[f"{prefix}_mae"] = mean_absolute_error(y[mask], pred[mask])
        out[f"{prefix}_rmse"] = root_mean_squared_error(y[mask], pred[mask])
    return out


class P1Experiment:
    """Baseline estacional contra HistGradientBoosting con calendario y rezagos."""

    def __init__(self, metadata, X, y):
        keep = metadata["station_id"].isin(eligible_stations(metadata, y)).to_numpy()
        self.metadata = metadata[keep].reset_index(drop=True)
        self.X = X[keep].reset_index(drop=True)
        self.y = y[keep].reset_index(drop=True)
        self.train = self.metadata["split"].eq("train").to_numpy()

    def fit(self):
        frame = pd.concat([self.metadata, self.X[["day_of_week", "hour_of_day"]]], axis=1)
        self.baseline = SeasonalMeanBaseline().fit(frame[self.train], self.y[self.train])
        self.candidate = make_candidate().fit(self.X.loc[self.train, FEATURE_COLUMNS], self.y[self.train])
        self.predictions = {
            "baseline": self.baseline.predict(frame),
            "candidato": np.clip(self.candidate.predict(self.X[FEATURE_COLUMNS]), 0, None),
        }
        self.metrics = {k: regression_metrics(self.y.to_numpy(), p, self.metadata["split"]) for k, p in self.predictions.items()}
        self.selected = "candidato" if self.metrics["candidato"]["val_mae"] < self.metrics["baseline"]["val_mae"] else "baseline"
        return self

    def test_frame(self):
        frame = self.metadata.assign(y=self.y, hour_of_day=self.X["hour_of_day"])
        return frame.loc[frame["split"].eq("test")]

    def log(self, executor):
        runs = {
            "baseline": ("P1-baseline-media-estacion-dia-hora", {"model": "seasonal_mean_station_dow_hour"}),
            "candidato": ("P1-candidato-hgb", {"model": "HistGradientBoostingRegressor", "features": ",".join(FEATURE_COLUMNS), **C.P1_HGB_PARAMS}),
        }
        params = {**common_params(self.metadata), "min_train_departures": C.P1_MIN_TRAIN_DEPARTURES, "selected_model": self.selected}
        tags = common_tags("P1", "regression", executor, "persona2", "viajes iniciados por estación en [t, t+1)")
        test = self.test_frame()
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            figures = [
                plots.p1_error_by_hour(test, {k: v[test.index] for k, v in self.predictions.items()}, folder / "p1_mae_por_hora.png"),
                plots.p1_station_week(test, self.predictions, folder / "p1_semana_estacion.png"),
            ]
            for name, (run_name, extra) in runs.items():
                error = (test["y"] - self.predictions[name][test.index]).abs().groupby(test["hour_of_day"]).mean()
                error.rename("test_mae").to_csv(folder / "error_por_hora.csv")
                (folder / "metrics.json").write_text(json.dumps(self.metrics[name], indent=2))
                (folder / "evaluation_notes.txt").write_text(
                    f"Seleccionado: {self.selected}. Criterio: menor val_mae. Prueba evaluada una sola vez.\n"
                )
                with question_run(run_name):
                    mlflow.set_tags({**tags, "model_role": name, "selected": str(name == self.selected).lower()})
                    mlflow.log_params({**params, **extra})
                    mlflow.log_metrics(self.metrics[name])
                    for file in ["metrics.json", "error_por_hora.csv", "evaluation_notes.txt"]:
                        mlflow.log_artifact(str(folder / file))
                    for figure in figures:
                        mlflow.log_artifact(str(figure), "figures")
            C.FIGURES.mkdir(parents=True, exist_ok=True)
            for figure in figures:
                (C.FIGURES / figure.name).write_bytes(figure.read_bytes())


def main():
    parser = argparse.ArgumentParser(description="P1: salidas por estación en la siguiente hora")
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "local"))
    experiment = P1Experiment(*load_tables()).fit()
    experiment.log(parser.parse_args().executor)
    print(json.dumps({"selected": experiment.selected, **experiment.metrics}, indent=2))


if __name__ == "__main__":
    main()
