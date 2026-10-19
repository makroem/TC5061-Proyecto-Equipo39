import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.preprocessing import TargetEncoder

from mibici_equipo39 import config as C
from mibici_equipo39 import plots
from mibici_equipo39.features import FEATURE_COLUMNS, eligible_stations, load_tables
from mibici_equipo39.modeling.tracking import common_params, common_tags, log_model_run

SPLITS = {"train": "train", "val": "validation", "test": "test"}


class SeasonalMeanBaseline:
    """Media de train por estación, día y hora; si falta, estación y hora; al final la global."""

    levels = (["station_id", "day_of_week", "hour_of_day"], ["station_id", "hour_of_day"])

    def fit(self, frame, y):
        self.means_ = [
            y.groupby([frame[k] for k in keys], observed=True).mean().rename("mean")
            for keys in self.levels
        ]
        self.global_ = float(y.mean())
        return self

    def predict(self, frame):
        pred = pd.Series(np.nan, index=frame.index)
        for keys, means in zip(self.levels, self.means_):
            pred = pred.fillna(frame[keys].join(means, on=keys)["mean"])
        return pred.fillna(self.global_).to_numpy()


ENCODED = ["te_station", "te_station_day_hour"]


class StationEncodedHGB:
    """HGB con calendario y media de salidas por estación y estación-día-hora ajustada solo en train.

    TargetEncoder usa validación cruzada dentro de train, así ninguna fila ve su propio objetivo
    y ningún día reservado entra a X.
    """

    def _keys(self, frame):
        station = frame["station_id"].astype(str)
        return pd.DataFrame(
            {
                "te_station": station,
                "te_station_day_hour": station
                + "|"
                + frame["day_of_week"].astype(str)
                + "|"
                + frame["hour_of_day"].astype(str),
            }
        )

    def fit(self, frame, y):
        self.encoder_ = TargetEncoder(
            target_type="continuous", cv=5, shuffle=True, random_state=C.SEED
        )
        encoded = pd.DataFrame(
            self.encoder_.fit_transform(self._keys(frame), y), columns=ENCODED, index=frame.index
        )
        self.model_ = HistGradientBoostingRegressor(**C.P1_HGB_PARAMS).fit(
            pd.concat([frame[FEATURE_COLUMNS], encoded], axis=1), y
        )
        return self

    def predict(self, frame):
        encoded = pd.DataFrame(
            self.encoder_.transform(self._keys(frame)), columns=ENCODED, index=frame.index
        )
        return np.clip(
            self.model_.predict(pd.concat([frame[FEATURE_COLUMNS], encoded], axis=1)), 0, None
        )


def regression_metrics(y, pred, split):
    out = {}
    for prefix, name in SPLITS.items():
        mask = split.eq(name).to_numpy()
        out[f"{prefix}_mae"] = mean_absolute_error(y[mask], pred[mask])
        out[f"{prefix}_rmse"] = root_mean_squared_error(y[mask], pred[mask])
    return out


class P1Experiment:
    """Baseline estacional contra HGB con calendario y codificación de estación, sin rezagos."""

    def __init__(self, metadata, X, y):
        keep = metadata["station_id"].isin(eligible_stations(metadata, y)).to_numpy()
        self.metadata = metadata[keep].reset_index(drop=True)
        self.X = X[keep].reset_index(drop=True)
        self.y = y[keep].reset_index(drop=True)
        self.train = self.metadata["split"].eq("train").to_numpy()

    def fit(self):
        frame = pd.concat([self.metadata, self.X], axis=1)
        self.baseline = SeasonalMeanBaseline().fit(frame[self.train], self.y[self.train])
        self.candidate = StationEncodedHGB().fit(frame[self.train], self.y[self.train])
        self.predictions = {
            "baseline": self.baseline.predict(frame),
            "candidato": self.candidate.predict(frame),
        }
        self.metrics = {
            k: regression_metrics(self.y.to_numpy(), p, self.metadata["split"])
            for k, p in self.predictions.items()
        }
        self.selected = (
            "candidato"
            if self.metrics["candidato"]["val_mae"] < self.metrics["baseline"]["val_mae"]
            else "baseline"
        )
        return self

    def test_frame(self):
        frame = self.metadata.assign(y=self.y, hour_of_day=self.X["hour_of_day"])
        return frame.loc[frame["split"].eq("test")]

    def log(self, executor):
        models = {
            "baseline": (
                "P1-baseline-media-estacion-dia-hora",
                {"model": "seasonal_mean_station_dow_hour"},
            ),
            "candidato": (
                "P1-candidato-hgb-estacion",
                {
                    "model": "HistGradientBoostingRegressor+TargetEncoder",
                    "features": ",".join(FEATURE_COLUMNS + ENCODED),
                    **C.P1_HGB_PARAMS,
                },
            ),
        }
        params = {
            **common_params(self.metadata),
            "min_train_departures": C.P1_MIN_TRAIN_DEPARTURES,
            "selected_model": self.selected,
        }
        tags = common_tags(
            "P1", "regression", executor, "persona2", "viajes iniciados por estación en [t, t+1)"
        )
        test = self.test_frame()
        C.FIGURES.mkdir(parents=True, exist_ok=True)
        figures = [
            plots.p1_error_by_hour(
                test,
                {k: p[test.index] for k, p in self.predictions.items()},
                C.FIGURES / "p1_mae_por_hora.png",
            ),
            plots.p1_station_week(test, self.predictions, C.FIGURES / "p1_semana_estacion.png"),
        ]
        for name, (run_name, extra) in models.items():
            error = (
                (test["y"] - self.predictions[name][test.index])
                .abs()
                .groupby(test["hour_of_day"])
                .mean()
            )
            texts = {
                "metrics.json": json.dumps(self.metrics[name], indent=2),
                "error_por_hora.csv": error.rename("test_mae").to_csv(),
                "evaluation_notes.txt": f"Seleccionado: {self.selected}. Criterio: menor val_mae. Prueba evaluada una sola vez.\n",
            }
            run_tags = {**tags, "model_role": name, "selected": str(name == self.selected).lower()}
            log_model_run(
                run_name, run_tags, {**params, **extra}, self.metrics[name], texts, figures
            )


def main():
    parser = argparse.ArgumentParser(description="P1: salidas por estación en la siguiente hora")
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "local"))
    experiment = P1Experiment(*load_tables()).fit()
    experiment.log(parser.parse_args().executor)
    print(json.dumps({"selected": experiment.selected, **experiment.metrics}, indent=2))


if __name__ == "__main__":
    main()
