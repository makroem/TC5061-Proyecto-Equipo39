import json
import uuid
from pathlib import Path

import numpy as np
import pandas as pd

from pathlib import Path

from loguru import logger
from tqdm import tqdm
import typer

from mibici_equipo39.config import (
    PROCESSED_DATA_DIR,
    INTERIM_DATA_DIR,
    EXTERNAL_DATA_DIR
)

app = typer.Typer()

def random_grouped_split(
    df,
    train_size=0.70,
    val_size=0.15,
    test_size=0.15,
    seed=39,
    manifest_path=None,
    data_version="1"
):
    """
    Divide por días completos estratificando por mes.

    Todos los registros de una fecha permanecen
    juntos en train, val o test.
    """

    if not np.isclose(
        train_size + val_size + test_size,
        1.0
    ):
        raise ValueError(
            "Los porcentajes deben sumar 1."
        )

    split_df = df.copy()

    split_df["date"] = (
        pd.to_datetime(split_df["hour"])
        .dt.date
    )

    split_df["month_strat"] = (
        pd.to_datetime(split_df["hour"])
        .dt.to_period("M")
        .astype(str)
    )

    rng = np.random.default_rng(seed)

    assignments = {}

    for month, month_data in split_df.groupby("month_strat"):

        days = (
            month_data["date"]
            .drop_duplicates()
            .values
        )

        rng.shuffle(days)

        n_days = len(days)

        n_train = int(train_size * n_days)
        n_val = int(val_size * n_days)

        train_days = days[:n_train]
        val_days = days[n_train:n_train + n_val]
        test_days = days[n_train + n_val:]

        for d in train_days:
            assignments[d] = "train"

        for d in val_days:
            assignments[d] = "validation"

        for d in test_days:
            assignments[d] = "test"

    split_df["split"] = (
        split_df["date"]
        .map(assignments)
    )

    split_id = str(uuid.uuid4())

    manifest = {
        "split_id": split_id,
        "seed": seed,
        "strategy":
            "random_days_month_stratified",
        "data_version": data_version,
        "days": {
            split_name: [
                str(day)
                for day, group in assignments.items()
                if group == split_name
            ]
            for split_name in [
                "train",
                "validation",
                "test"
            ]
        }
    }

    if manifest_path is not None:

        manifest_path = Path(manifest_path)

        with open(
            manifest_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                manifest,
                f,
                indent=2,
                ensure_ascii=False
            )

    return split_df, manifest

def make_events(clean_departures, clean_arrivals):
    """
    Genera eventos de salida (-1) y llegada (+1).

    """

    departures = clean_departures.copy()
    arrivals = clean_arrivals.copy()

    departures["event"] = -1
    arrivals["event"] = 1

    departures = departures[
        ["station_id", "timestamp", "event"]
    ]

    arrivals = arrivals[
        ["station_id", "timestamp", "event"]
    ]

    events = pd.concat(
        [departures, arrivals],
        ignore_index=True
    )

    events["timestamp"] = pd.to_datetime(
        events["timestamp"]
    )

    events = events.sort_values(
        ["timestamp", "station_id"]
    ).reset_index(drop=True)

    return events


def aggregate_hourly(events, stations, config=None):
    """
    Agrega eventos por estación-hora y completa los
    periodos faltantes con ceros.
    """


    df = events.copy()

    # intervalos [t, t+1)
    df["hour"] = df["timestamp"].dt.floor("h")

    departures = (
        df[df["event"] == -1]
        .groupby(["station_id", "hour"])
        .size()
        .reset_index(name="departures")
    )

    arrivals = (
        df[df["event"] == 1]
        .groupby(["station_id", "hour"])
        .size()
        .reset_index(name="arrivals")
    )

    hourly = departures.merge(
        arrivals,
        on=["station_id", "hour"],
        how="outer"
    )

    hourly["departures"] = (
        hourly["departures"]
        .fillna(0)
        .astype(int)
    )

    hourly["arrivals"] = (
        hourly["arrivals"]
        .fillna(0)
        .astype(int)
    )

    all_hours = pd.date_range(
        start=hourly["hour"].min(),
        end=hourly["hour"].max(),
        freq="h"
    )

    if "station_id" not in stations.columns:
        stations = stations.rename(
            columns={"id": "station_id"}
         )

    all_stations = (
    stations["station_id"]
    .drop_duplicates()
    .sort_values()
    )

    full_index = pd.MultiIndex.from_product(
        [all_stations, all_hours],
        names=["station_id", "hour"]
    )

    hourly = (
        hourly
        .set_index(["station_id", "hour"])
        .reindex(full_index)
        .fillna(0)
        .reset_index()
    )

    hourly["departures"] = hourly["departures"].astype(int)
    hourly["arrivals"] = hourly["arrivals"].astype(int)

    return hourly


def add_calendar_features(df):
    """
    Agrega variables calendarias y cíclicas.
    """

    df = df.copy()

    df["hour_of_day"] = df["hour"].dt.hour

    df["day_of_week"] = (
        df["hour"].dt.dayofweek
    )

    df["month"] = (
        df["hour"].dt.month
    )

    df["is_weekend"] = (
        df["day_of_week"] >= 5
    ).astype(int)

    df["hour_sin"] = np.sin(
        2 * np.pi * df["hour_of_day"] / 24
    )

    df["hour_cos"] = np.cos(
        2 * np.pi * df["hour_of_day"] / 24
    )

    df["month_sin"] = np.sin(
        2 * np.pi * df["month"] / 12
    )

    df["month_cos"] = np.cos(
        2 * np.pi * df["month"] / 12
    )

    return df


def add_lagged_features(df):
    """
    Placeholder para una futura evaluación temporal.

    Los rezagos y medias móviles deberán construirse
    exclusivamente utilizando información previa al
    instante de predicción.
    """

    return df

def build_supervised_tables(df, p2_labels=None, data_version="1"):
    """
   Construye matrices supervisadas para P1 y P2.
   Requiere que el dataframe ya tenga:
       -split
       - variables calendario
   """

    feature_columns = [
       "hour_of_day",
       "day_of_week",
       "month",
       "is_weekend",
       "hour_sin",
       "hour_cos",
       "month_sin",
       "month_cos",
    ]

    metadata = df[
       ["station_id", "hour", "split"]
    ].copy()

    metadata = metadata.rename(
       columns={"hour": "prediction_time"}
    )

    metadata["data_version"] = data_version

    X = df[feature_columns].copy()
    # Conteo de salidas observado en la hora t, t+1
    y_p1 = df["departures"].copy()

    result = {
       "metadata": metadata,
       "X": X,
       "y_p1": y_p1,
    }

    if p2_labels is not None:
        result["y_p2"] = (p2_labels.copy())

    return result
    

@app.command()
def build():
    """
    Construye el pipeline completo de features:

    1. Carga vistas limpias de salidas y llegadas.
    2. Genera eventos.
    3. Agrega a nivel estación-hora.
    4. Agrega variables calendario.
    5. Genera partición reproducible.
    6. Construye tablas supervisadas.
    7. Guarda artefactos en data/processed.
    """
    logger.info("Building features...")

    departures = pd.read_parquet(
        INTERIM_DATA_DIR / "departures"
    )

    arrivals = pd.read_parquet(
        INTERIM_DATA_DIR / "arrivals"
    )

    stations = pd.read_csv(
        EXTERNAL_DATA_DIR / "nomenclatura_2026_09.csv"
    )

    logger.info(
        f"Departures: {departures.shape}"
    )

    logger.info(
        f"Arrivals: {arrivals.shape}"
    )

    events = make_events(
        departures,
        arrivals
    )

    logger.info(
        f"Events: {events.shape}"
    )

    hourly = aggregate_hourly(
        events,
        stations
    )

    logger.info(
        f"Hourly: {hourly.shape}"
    )


    hourly = add_calendar_features(
        hourly
    )


    processed_references = (
        Path("references")
        / "split_manifest.json"
    )

    hourly, manifest = (
        random_grouped_split(
            hourly,
            seed=39,
            manifest_path=processed_references
        )
    )

    logger.info(
        f"Split ID: {manifest['split_id']}"
    )


    tables = build_supervised_tables(
        hourly
    )

    metadata = tables["metadata"]
    X = tables["X"]
    y_p1 = tables["y_p1"]


    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    metadata.to_parquet(
        PROCESSED_DATA_DIR
        / "metadata.parquet"
    )

    X.to_parquet(
        PROCESSED_DATA_DIR
        / "X_p1.parquet"
    )

    y_p1.to_frame(
        name="target_departures"
    ).to_parquet(
        PROCESSED_DATA_DIR
        / "y_p1.parquet"
    )

    logger.success(
        "Feature generation complete."
    )
    
if __name__ == "__main__":
    app()
