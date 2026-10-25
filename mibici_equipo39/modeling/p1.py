import argparse
import json
import os

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sklearn.preprocessing import TargetEncoder

from sklearn.ensemble import (RandomForestRegressor, HistGradientBoostingRegressor)
import time
import pickle

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

def build_candidate(name):
    if name == "p1_hgb_100":
        return StationEncodedRegressor( 
            HistGradientBoostingRegressor(**C.P1_HGB_100_PARAMS))
    if name == "p1_hgb_200":
        return StationEncodedRegressor(
            HistGradientBoostingRegressor(**C.P1_HGB_200_PARAMS))
    if name == "p1_rf_300":
        return StationEncodedRegressor(
            RandomForestRegressor(**C.P1_RF_300_PARAMS))
    raise ValueError(f"Modelo desconocido {name}")
    


class StationEncodedRegressor:
    """HGB con calendario y media de salidas por estación y estación-día-hora ajustada solo en train.

    TargetEncoder usa validación cruzada dentro de train, así ninguna fila ve su propio objetivo
    y ningún día reservado entra a X.
    """

    def __init__(self, estimator):
        self.estimator= estimator

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
        self.model_ = self.estimator.fit(pd.concat([frame[FEATURE_COLUMNS], encoded], axis=1), y)
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
        start = time.perf_counter()
        
        self.models ={ }
        self.fit_seconds = { }
        self.predict_ms_per_1000 = { }
        self.model_sizes = { }
        
        self.baseline = SeasonalMeanBaseline().fit(frame[self.train], self.y[self.train])
        self.model_sizes["baseline"] = model_bytes(self.baseline)
        
        self.fit_seconds["baseline"]=(time.perf_counter() -start)
        
        candidate_names=[ "p1_hgb_100","p1_hgb_200", "p1_rf_300"]
        
        
        for n in candidate_names:   
            start = time.perf_counter()
            model=build_candidate(n).fit(
                frame[self.train],
                self.y[self.train])
            
            self.model_sizes[n]=model_bytes(model)
            self.fit_seconds[n] = (time.perf_counter() - start)
            self.models[n] = model
        
        start = time.perf_counter()
        baseline_pred=self.baseline.predict(frame)
        elapsed = time.perf_counter() -start
        
        self.predict_ms_per_1000["baseline"]= (elapsed * 1000 /len(frame)*1000)
        
        self.predictions = {
            "baseline": baseline_pred}
     
        
        for n, model in self.models.items():
           start = time.perf_counter()
           pred=model.predict(frame)
           elapsed=time.perf_counter()-start
           self.predict_ms_per_1000[n]=(elapsed*1000 /len(frame)*1000)
           self.predictions[n]= pred
        
           
        validation = self.metadata["split"].eq("validation")
        dates = pd.to_datetime(self.metadata.loc[validation, "prediction_time"])
        months = dates.dt.to_period("M")
        
        self.monthly_mae= { }
    
        for name, pred in self.predictions.items():
            frame_month = pd.DataFrame(
                {"month": months.astype(str),
                 "actual": self.y.loc[validation].to_numpy(),
                 "pred": pred[validation.to_numpy()],}
                )
            
            monthly_mae = (frame_month.assign(error=lambda x: (x["actual"] - x["pred"]).abs())
                           .groupby("month")["error"].mean())
            
            self.monthly_mae[name] = monthly_mae
        
        self.metrics = {
            k: regression_metrics(self.y.to_numpy(), p, self.metadata["split"])
            for k, p in self.predictions.items()
        }
        
        
        for n in self.metrics:
            self.metrics[n]["fit_seconds"]=self.fit_seconds[n]
            self.metrics[n]["predict_ms_per_1000"]= self.predict_ms_per_1000[n]
            self.metrics[n]["model_bytes"]= self.model_sizes[n]
        
        best_mae = min(round(m["val_mae"], 6) for m in self.metrics.values())
        tied = [name for name, m in self.metrics.items()
                if round(m["val_mae"], 6) == best_mae]
        if "baseline" in tied:
            self.selected = "baseline"
        else:
            self.selected = min(tied, key=lambda name: (
            self.metrics[name]["predict_ms_per_1000"],
            self.metrics[name]["model_bytes"],
            ),
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
            "p1_hgb_100": (
                "P1-hgb-100",
                {
                    "model": "HistGradientBoostingRegressor+TargetEncoder",
                    "features": ",".join(FEATURE_COLUMNS + ENCODED),
                    **C.P1_HGB_100_PARAMS,
                },
            ),
            "p1_hgb_200": (
                "P1-hgb-200",
                {
                    "model": "HistGradientBoostingRegressor+TargetEncoder",
                    "features": ",".join(FEATURE_COLUMNS + ENCODED),
                    **C.P1_HGB_200_PARAMS,
                },
            ),
            
            "p1_rf_300": (
                "P1-rf-300",
                {
                    "model": "RandomForestRegressor+TargetEncoder",
                    "features": ",".join(FEATURE_COLUMNS + ENCODED),
                    **C.P1_RF_300_PARAMS,
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
        selected_pred=self.predictions[self.selected][test.index]
        figures = [
            plots.p1_error_by_hour(
                test,
                {k: p[test.index] for k, p in self.predictions.items()},
                C.FIGURES / "p1_mae_por_hora.png",
            ),
            plots.p1_station_week(
                test, self.predictions, C.FIGURES / "p1_semana_estacion.png",
                ),
            plots.p1_real_vs_predicho(
                test["y"],
                selected_pred,
                C.FIGURES / "real_vs_predicho.png",),
            plots.p1_residuales(
                test["y"],
                selected_pred,
                C.FIGURES / "residuales.png")
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
                "monthly_mae.csv": self.monthly_mae[name].rename("mae").to_csv(),
                "evaluation_notes.txt": (f"Seleccionado: {self.selected}."
                                         f"Criterio: menor val_mae." "Prueba evaluada una sola vez.\n"),
            }
            run_tags = {**tags, "model_role": name, "selected": str(name == self.selected).lower()}
            log_model_run(
                run_name, run_tags, {**params, **extra}, self.metrics[name], texts, figures
            )


def model_bytes(model):
    return len (pickle.dumps(model))

def main():
    parser = argparse.ArgumentParser(description="P1: salidas por estación en la siguiente hora")
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "local"))
    experiment = P1Experiment(*load_tables()).fit()
    experiment.log(parser.parse_args().executor)
    print(json.dumps({"selected": experiment.selected, **experiment.metrics}, indent=2))


if __name__ == "__main__":
    main()
