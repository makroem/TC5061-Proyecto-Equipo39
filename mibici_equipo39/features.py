import hashlib
import json
from pathlib import Path

from loguru import logger
import numpy as np
import pandas as pd
import typer

from mibici_equipo39 import config as C

app = typer.Typer()

SPLIT_PATH = C.REFERENCES / "split_manifest.json"
LAGS = (1, 2, 24, 168)
WINDOWS = (24, 168)
CALENDAR_FEATURES = [
    "hour_of_day", "day_of_week", "month", "is_weekend",
    "hour_sin", "hour_cos", "month_sin", "month_cos",
]
LAG_FEATURES = (
    [f"{p}_lag_{k}" for p in ("dep", "arr") for k in LAGS]
    + [f"{p}_mean_{w}" for p in ("dep", "arr") for w in WINDOWS]
    + ["net_lag_1", "net_sum_24"]
)
# El reparto aleatorio de días no aísla los rezagos entre conjuntos.
# Los objetivos reservados nunca deben reaparecer en X de entrenamiento.
FEATURE_COLUMNS = CALENDAR_FEATURES.copy()


def random_grouped_split(df, seed=C.SEED, manifest_path=None, data_version="1"):
    """
    Divide por días completos estratificando por mes (70/15/15 de config.py).

    Ningún día queda en dos conjuntos y todos los meses aparecen en train, val y test.
    El split_id es el hash del mapa de días, así que la misma semilla da el mismo id.
    """
    split_df = df.copy()
    split_df["date"] = split_df["hour"].dt.normalize()
    rng = np.random.default_rng(seed)
    assignments = {}
    for _, days in split_df.groupby(split_df["date"].dt.to_period("M"))["date"]:
        days = np.sort(days.unique())
        rng.shuffle(days)
        cut_train = int(np.floor(C.TRAIN_SIZE * len(days) + 0.5))
        cut_val = int(np.floor((C.TRAIN_SIZE + C.VAL_SIZE) * len(days) + 0.5))
        for i, day in enumerate(days):
            assignments[pd.Timestamp(day)] = "train" if i < cut_train else "validation" if i < cut_val else "test"
    split_df["split"] = split_df["date"].map(assignments)

    days = {name: sorted(d.strftime("%Y-%m-%d") for d, s in assignments.items() if s == name)
            for name in ["train", "validation", "test"]}
    content = {"seed": seed, "strategy": C.SPLIT_STRATEGY, "data_version": data_version, "days": days}
    split_id = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    manifest = {"split_id": split_id, **content}
    if manifest_path is not None:
        path = Path(manifest_path)
        if not path.is_file():
            raise FileNotFoundError("Falta split_manifest.json confirmado; crear una partición requiere un PR explícito.")
        confirmed = json.loads(path.read_text(encoding="utf-8"))
        if confirmed != manifest:
            raise ValueError("La partición no coincide con split_manifest.json; no se modificó el manifiesto confirmado.")
    return split_df.drop(columns="date"), manifest


def make_events(clean_departures, clean_arrivals):
    """
    Genera eventos de salida (-1, en el inicio) y llegada (+1, en el fin).

    Las salidas no dependen del fin del viaje porque al pronosticar ese fin aún no se conoce.
    """
    departures = clean_departures[["station_id", "timestamp"]].assign(event=-1)
    arrivals = clean_arrivals[["station_id", "timestamp"]].assign(event=1)
    events = pd.concat([departures, arrivals], ignore_index=True)
    events["station_id"] = events["station_id"].astype("string")
    events["timestamp"] = pd.to_datetime(events["timestamp"])
    return events.sort_values(["timestamp", "station_id"]).reset_index(drop=True)


def aggregate_hourly(events, stations, start=C.SOURCE_START, end=C.SOURCE_END_EXCLUSIVE):
    """
    Cuenta salidas y llegadas por estación en intervalos [t, t+1) y completa con ceros.

    Sin la malla completa se pierden las horas sin viajes y los rezagos dejan de ser horas reales.
    Solo entran estaciones del catálogo, que P2 y P3 necesitan para capacidad y coordenadas.
    """
    df = events.loc[events["station_id"].isin(stations["station_id"])].copy()
    df["hour"] = df["timestamp"].dt.floor("h")
    df = df.loc[df["hour"].ge(start) & df["hour"].lt(end)]
    counts = (
        df.groupby(["station_id", "hour", "event"], observed=True).size()
        .unstack("event", fill_value=0)
        .reindex(columns=[-1, 1], fill_value=0)
        .rename(columns={-1: "departures", 1: "arrivals"})
    )
    full_index = pd.MultiIndex.from_product(
        [sorted(df["station_id"].unique()), pd.date_range(start, end, freq="h", inclusive="left")],
        names=["station_id", "hour"],
    )
    hourly = counts.reindex(full_index, fill_value=0).reset_index()
    hourly.columns.name = None
    hourly["station_id"] = hourly["station_id"].astype("string")
    hourly[["departures", "arrivals"]] = hourly[["departures", "arrivals"]].astype("int32")
    return hourly


def add_calendar_features(df):
    """
    Agrega hora, día, mes, fin de semana y sus versiones cíclicas.

    Se conocen antes de la hora objetivo y capturan los picos de traslado (P1, P2)
    y la diferencia entre semana y fin de semana (P3).
    """
    df = df.copy()
    df["hour_of_day"] = df["hour"].dt.hour
    df["day_of_week"] = df["hour"].dt.dayofweek
    df["month"] = df["hour"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["hour_sin"] = np.sin(2 * np.pi * df["hour_of_day"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["hour_of_day"] / 24)
    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    return df


def add_lagged_features(df):
    """
    Agrega rezagos y medias móviles por estación usando solo horas anteriores a t.

    shift(1) va antes de rolling, así la hora objetivo nunca entra en su propia variable.
    Miden la actividad reciente de cada estación, que explica la demanda de la siguiente
    hora (P1) y la presión acumulada de salidas contra llegadas (P2).
    """
    df = df.sort_values(["station_id", "hour"]).reset_index(drop=True)
    by_station = df.groupby("station_id", sort=False, observed=True)
    steps = by_station["hour"].diff().dropna()
    if by_station.size().nunique() != 1 or not steps.eq(pd.Timedelta("1h")).all():
        raise ValueError("La malla estación-hora no está completa.")

    def rolling(series, window, how):
        grouped = series.groupby(df["station_id"], sort=False, observed=True).rolling(window, min_periods=window)
        return getattr(grouped, how)().reset_index(level=0, drop=True).sort_index()

    net = df["arrivals"] - df["departures"]
    new = {}
    for column, prefix in [("departures", "dep"), ("arrivals", "arr")]:
        for lag in LAGS:
            new[f"{prefix}_lag_{lag}"] = by_station[column].shift(lag)
        past = by_station[column].shift(1)
        for window in WINDOWS:
            new[f"{prefix}_mean_{window}"] = rolling(past, window, "mean")
    past_net = net.groupby(df["station_id"], sort=False, observed=True).shift(1)
    new["net_lag_1"] = past_net
    new["net_sum_24"] = rolling(past_net, 24, "sum")
    return pd.concat([df, pd.DataFrame(new).astype("float32")], axis=1)


def intra_hour_extremes(events, start=C.SOURCE_START, end=C.SOURCE_END_EXCLUSIVE):
    """
    Mínimo y máximo del flujo acumulado (llegadas menos salidas) dentro de cada hora.

    El flujo parte de cero y los eventos con el mismo timestamp se suman antes de acumular.
    Describe la hora objetivo, así que solo sirve para construir etiquetas de P2, nunca como X.
    """
    df = events.assign(hour=events["timestamp"].dt.floor("h"))
    df = df.loc[df["hour"].ge(start) & df["hour"].lt(end)]
    net = df.groupby(["station_id", "hour", "timestamp"], observed=True)["event"].sum()
    by_hour = net.groupby(level=["station_id", "hour"], observed=True).cumsum().groupby(level=["station_id", "hour"], observed=True)
    return pd.DataFrame({"flow_min": by_hour.min().clip(upper=0), "flow_max": by_hour.max().clip(lower=0)})


def proxy_labels(flow_min, flow_max, capacity, occupancy=C.P2_INITIAL_OCCUPANCY, margin=C.P2_MARGIN):
    """
    Riesgo aproximado con ocupación inicial hipotética: B*(u) = occupancy * capacidad + flujo.

    y_bikes = 1 si el mínimo de B* llega a margin * capacidad; y_docks = 1 si el máximo
    llega a (1 - margin) * capacidad. No se recorta B* para no esconder la presión acumulada.
    """
    start = occupancy * capacity
    y_bikes = (start + flow_min).le(margin * capacity).astype("int8")
    y_docks = (start + flow_max).ge((1 - margin) * capacity).astype("int8")
    return y_bikes, y_docks


def make_capacity_proxy_targets(hourly, events, stations):
    """
    Etiquetas de P2 alineadas con la malla: riesgo de quedarse sin bicicletas o sin anclajes.

    Usa la capacidad publicada solo para definir la etiqueta; las estaciones sin capacidad
    válida quedan en NaN y se excluyen antes de entrenar. MiBici no publica inventario.
    """
    valid = stations.loc[stations["valid_capacity"].fillna(False), ["station_id", "capacity"]]
    targets = hourly[["station_id", "hour"]].merge(valid, on="station_id", how="left")
    keys = pd.MultiIndex.from_frame(targets[["station_id", "hour"]])
    extremes = intra_hour_extremes(events).reindex(keys, fill_value=0)
    targets["flow_min"] = extremes["flow_min"].to_numpy().astype("int32")
    targets["flow_max"] = extremes["flow_max"].to_numpy().astype("int32")
    targets["capacity"] = targets["capacity"].astype("float64")
    y_bikes, y_docks = proxy_labels(targets["flow_min"], targets["flow_max"], targets["capacity"])
    has_capacity = targets["capacity"].notna()
    targets["y_bikes"] = y_bikes.where(has_capacity)
    targets["y_docks"] = y_docks.where(has_capacity)
    return targets[["capacity", "flow_min", "flow_max", "y_bikes", "y_docks"]]


def build_supervised_tables(df, p2_labels=None, data_version="1"):
    """
    Construye metadata, X y objetivos. P1 es el conteo de salidas en [t, t+1).

    X solo lleva calendario. Los rezagos se excluyen para no reutilizar objetivos
    reservados mediante las fechas mezcladas del reparto aleatorio.
    """
    metadata = df[["station_id", "hour", "split"]].rename(columns={"hour": "prediction_time"})
    metadata["data_version"] = data_version
    result = {"metadata": metadata, "X": df[FEATURE_COLUMNS].copy(), "y_p1": df["departures"].copy()}
    if p2_labels is not None:
        result["y_p2"] = p2_labels.copy()
    return result


def eligible_stations(metadata, y_p1, min_departures=C.P1_MIN_TRAIN_DEPARTURES):
    """Estaciones con suficientes salidas en train; se fija sin mirar val ni test."""
    train = metadata["split"].eq("train")
    totals = y_p1[train].groupby(metadata.loc[train, "station_id"], observed=True).sum()
    return sorted(totals.index[totals.ge(min_departures)])


def load_tables():
    """Lee las tablas que deja build() en data/processed."""
    metadata = pd.read_parquet(C.PROCESSED / "metadata.parquet")
    X = pd.read_parquet(C.PROCESSED / "X_p1.parquet")
    y_p1 = pd.read_parquet(C.PROCESSED / "y_p1.parquet")["target_departures"]
    return metadata, X, y_p1


def load_p2_targets():
    """Etiquetas de P2 alineadas fila por fila con metadata."""
    return pd.read_parquet(C.PROCESSED / "y_p2.parquet")


@app.command()
def build():
    """Construye calendario y tablas con una partición confirmada, sin rezagos en X."""
    data_version = json.loads((C.REFERENCES / "data_manifest.json").read_text())["data_version"]
    departures = pd.read_parquet(C.INTERIM / "departures", columns=["station_id", "timestamp"])
    arrivals = pd.read_parquet(C.INTERIM / "arrivals", columns=["station_id", "timestamp"])
    stations = pd.read_parquet(C.PROCESSED / "stations.parquet")

    events = make_events(departures, arrivals)
    hourly = aggregate_hourly(events, stations)
    hourly = add_calendar_features(hourly)
    hourly = hourly.loc[hourly["hour"].ge(C.FEATURES_START)].reset_index(drop=True)
    hourly, manifest = random_grouped_split(hourly, manifest_path=SPLIT_PATH, data_version=data_version)
    if hourly[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Quedan variables de calendario vacías.")

    p2_labels = make_capacity_proxy_targets(hourly, events, stations)
    tables = build_supervised_tables(hourly, p2_labels=p2_labels, data_version=data_version)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    tables["metadata"].to_parquet(C.PROCESSED / "metadata.parquet", index=False)
    tables["X"].to_parquet(C.PROCESSED / "X_p1.parquet", index=False)
    tables["y_p1"].to_frame("target_departures").to_parquet(C.PROCESSED / "y_p1.parquet", index=False)
    tables["y_p2"].to_parquet(C.PROCESSED / "y_p2.parquet", index=False)
    logger.info(f"P2: y_bikes {p2_labels['y_bikes'].mean():.4f}, y_docks {p2_labels['y_docks'].mean():.4f}")
    counts = {k: len(v) for k, v in manifest["days"].items()}
    logger.success(f"{len(hourly)} filas, {hourly['station_id'].nunique()} estaciones, split {manifest['split_id'][:12]} {counts}")


if __name__ == "__main__":
    app()
