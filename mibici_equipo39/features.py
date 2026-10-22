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
CALENDAR_FEATURES = [
    "hour_of_day",
    "day_of_week",
    "month",
    "is_weekend",
    "hour_sin",
    "hour_cos",
    "month_sin",
    "month_cos",
]
# Solo se usan entradas disponibles antes de la hora objetivo.
FEATURE_COLUMNS = CALENDAR_FEATURES.copy()


def chronological_split(df, seed=C.SEED, manifest_path=None, data_version="1"):
    """
    Divide periodos contiguos sin entrenar con fechas posteriores a validación o prueba.

    Train: octubre a mayo; validación: junio y julio; test: agosto y septiembre.
    El manifiesto incluye los límites y los días reales, se verifica sin sobrescribirlo.
    """
    split_df = df.copy()
    split_df["date"] = split_df["hour"].dt.normalize()
    start, train_end, val_end, end = map(pd.Timestamp, (
        C.FEATURES_START, C.TRAIN_END_EXCLUSIVE,
        C.VALIDATION_END_EXCLUSIVE, C.SOURCE_END_EXCLUSIVE))
    if not start < train_end < val_end < end:
        raise ValueError("Los límites temporales deben estar ordenados.")
    if split_df.empty or not split_df["date"].between(start, end, inclusive="left").all():
        raise ValueError("La malla debe estar dentro del rango temporal confirmado.")
    split_df["split"] = np.where(split_df["date"].lt(train_end), "train",
                                 np.where(split_df["date"].lt(val_end), "validation", "test"))
    assignments = dict(zip(split_df["date"], split_df["split"]))

    days = {
        name: sorted(d.strftime("%Y-%m-%d") for d, s in assignments.items() if s == name)
        for name in ["train", "validation", "test"]
    }
    content = {
        "seed": seed,
        "strategy": C.SPLIT_STRATEGY,
        "version": C.SPLIT_VERSION,
        "boundaries": {"start": C.FEATURES_START,
                       "train_end_exclusive": C.TRAIN_END_EXCLUSIVE,
                       "validation_end_exclusive": C.VALIDATION_END_EXCLUSIVE,
                       "end_exclusive": C.SOURCE_END_EXCLUSIVE},
        "data_version": data_version,
        "days": days,
    }
    split_id = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
    manifest = {"split_id": split_id, **content}
    if any(not days[name] for name in days):
        raise ValueError("Los tres periodos deben contener días observados.")
    if manifest_path is not None:
        path = Path(manifest_path)
        if not path.is_file():
            raise FileNotFoundError(
                "Falta split_manifest.json confirmado; crear una partición requiere un PR explícito."
            )
        confirmed = json.loads(path.read_text(encoding="utf-8"))
        if confirmed != manifest:
            raise ValueError(
                "La partición no coincide con split_manifest.json; no se modificó el manifiesto confirmado."
            )
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

    Sin la malla completa se pierden las horas sin viajes y el modelo sobreestima la demanda.
    Solo entran estaciones del catálogo, que P2 y P3 necesitan para capacidad y coordenadas.
    """
    df = events.loc[events["station_id"].isin(stations["station_id"])].copy()
    df["hour"] = df["timestamp"].dt.floor("h")
    df = df.loc[df["hour"].ge(start) & df["hour"].lt(end)]
    counts = (
        df.groupby(["station_id", "hour", "event"], observed=True)
        .size()
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


def intra_hour_extremes(events, start=C.SOURCE_START, end=C.SOURCE_END_EXCLUSIVE):
    """
    Mínimo y máximo del flujo acumulado (llegadas menos salidas) dentro de cada hora.

    El flujo parte de cero y los eventos con el mismo timestamp se suman antes de acumular.
    Describe la hora objetivo, así que solo sirve para construir etiquetas de P2, nunca como X.
    """
    df = events.assign(hour=events["timestamp"].dt.floor("h"))
    df = df.loc[df["hour"].ge(start) & df["hour"].lt(end)]
    net = df.groupby(["station_id", "hour", "timestamp"], observed=True)["event"].sum()
    by_hour = (
        net.groupby(level=["station_id", "hour"], observed=True)
        .cumsum()
        .groupby(level=["station_id", "hour"], observed=True)
    )
    return pd.DataFrame(
        {"flow_min": by_hour.min().clip(upper=0), "flow_max": by_hour.max().clip(lower=0)}
    )


def proxy_labels(
    flow_min, flow_max, capacity, occupancy=C.P2_INITIAL_OCCUPANCY, margin=C.P2_MARGIN
):
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

    X solo lleva calendario conocido antes de predecir. Ni flujos ni etiquetas entran a X.
    """
    metadata = df[["station_id", "hour", "split"]].rename(columns={"hour": "prediction_time"})
    metadata["data_version"] = data_version
    result = {
        "metadata": metadata,
        "X": df[FEATURE_COLUMNS].copy(),
        "y_p1": df["departures"].copy(),
    }
    if p2_labels is not None:
        result["y_p2"] = p2_labels.copy()
    return result


def eligible_stations(metadata, y_p1, min_departures=C.P1_MIN_TRAIN_DEPARTURES):
    """Estaciones con suficientes salidas en train; se fija sin mirar val ni test."""
    train = metadata["split"].eq("train")
    totals = y_p1[train].groupby(metadata.loc[train, "station_id"], observed=True).sum()
    return sorted(totals.index[totals.ge(min_departures)])


def station_usage_profiles(frame, station_ids, weight=None):
    """Perfil P3 de 48 proporciones horarias, sin coordenadas ni objetivos de otros periodos.

    Promedia salidas por hora y tipo de día (laboral o fin de semana), incluyendo ceros
    de la malla, y normaliza cada bloque de 24 horas a suma uno. Las ponderaciones
    opcionales permiten remuestrear días de train sin duplicar millones de filas.
    La elegibilidad se fija externamente usando solo viajes de train.
    """
    f = frame.loc[frame["station_id"].isin(station_ids)].copy()
    f["weekend"] = f["prediction_time"].dt.dayofweek.ge(5).astype(int)
    f["hour"] = f["prediction_time"].dt.hour
    f["weight"] = f[weight].to_numpy() if weight else 1.0
    if f["weight"].lt(0).any():
        raise ValueError("Los pesos del perfil no pueden ser negativos.")
    f["weighted_departures"] = f["departures"] * f["weight"]
    groups = f.groupby(["station_id", "weekend", "hour"], observed=True)
    means = groups["weighted_departures"].sum() / groups["weight"].sum().replace(0, np.nan)
    columns = pd.MultiIndex.from_product([[0, 1], range(24)], names=["weekend", "hour"])
    profile = means.unstack(["weekend", "hour"]).reindex(index=station_ids, columns=columns).fillna(0)
    for day_type in (0, 1):
        block = profile[day_type]
        profile.loc[:, day_type] = block.div(block.sum(axis=1).replace(0, 1), axis=0).to_numpy()
    profile.columns = [f"{'weekend' if d else 'weekday'}_hour_{h:02d}" for d, h in columns]
    return profile.astype(float)


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
    hourly, manifest = chronological_split(
        hourly, manifest_path=SPLIT_PATH, data_version=data_version
    )
    if hourly[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Quedan variables de calendario vacías.")

    p2_labels = make_capacity_proxy_targets(hourly, events, stations)
    tables = build_supervised_tables(hourly, p2_labels=p2_labels, data_version=data_version)
    C.PROCESSED.mkdir(parents=True, exist_ok=True)
    tables["metadata"].to_parquet(C.PROCESSED / "metadata.parquet", index=False)
    tables["X"].to_parquet(C.PROCESSED / "X_p1.parquet", index=False)
    tables["y_p1"].to_frame("target_departures").to_parquet(
        C.PROCESSED / "y_p1.parquet", index=False
    )
    tables["y_p2"].to_parquet(C.PROCESSED / "y_p2.parquet", index=False)
    logger.info(
        f"P2: y_bikes {p2_labels['y_bikes'].mean():.4f}, y_docks {p2_labels['y_docks'].mean():.4f}"
    )
    counts = {k: len(v) for k, v in manifest["days"].items()}
    logger.success(
        f"{len(hourly)} filas, {hourly['station_id'].nunique()} estaciones, split {manifest['split_id'][:12]} {counts}"
    )


if __name__ == "__main__":
    app()
