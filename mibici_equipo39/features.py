import numpy as np
import pandas as pd


def make_events(clean_departures, clean_arrivals):
    """
    Genera eventos de salida (-1) y llegada (+1).

    Parameters
    ----------
    clean_departures : pd.DataFrame
        Tabla de salidas limpias.

    clean_arrivals : pd.DataFrame
        Tabla de llegadas limpias.

    Returns
    -------
    pd.DataFrame
        Tabla consolidada de eventos.
    """

    departures = clean_departures.copy()
    arrivals = clean_arrivals.copy()

    departures = departures.rename(
        columns={"started_at": "timestamp"}
    )
    departures["event"] = -1

    arrivals = arrivals.rename(
        columns={"ended_at": "timestamp"}
    )
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







