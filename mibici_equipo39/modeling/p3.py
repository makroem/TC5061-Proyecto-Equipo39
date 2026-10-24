"""P3: perfiles de uso de estaciones ajustados solo con el periodo de entrenamiento."""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle
from time import perf_counter
from sklearn.cluster import KMeans
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import adjusted_rand_score, davies_bouldin_score, silhouette_score
from sklearn.pipeline import Pipeline

from mibici_equipo39 import config as C
from mibici_equipo39.features import load_tables, station_usage_profiles
from mibici_equipo39.modeling.tracking import common_params, common_tags, log_model_run

def build_p3_pipeline(family, params, seed=C.SEED):
    """Construye scaler + estimador para una variante de P3 sin ajustar datos."""
    family = str(family).strip().lower()
    resolved = dict(params)
    resolved.setdefault("random_state", seed)

    if family == "kmeans":
        model = KMeans(**resolved)
    elif family == "gmm":
        model = GaussianMixture(**resolved)
    else:
        raise ValueError(f"familia de P3 no soportada: {family}")

    return Pipeline([
        ("scaler", StandardScaler()),
        ("model", model),
    ])

def p3_model_cost_metrics(
    pipeline,
    predict_profiles,
    fit_seconds,
    repeats=5,
):
    """Calcula costo comparable de ajuste, inferencia y tamaño serializado."""
    if repeats < 1:
        raise ValueError("repeats debe ser al menos 1")

    if len(predict_profiles) == 0:
        raise ValueError(
            "predict_profiles no puede estar vacío"
        )

    timings = []

    for _ in range(repeats):
        start = perf_counter()
        pipeline.predict(predict_profiles)
        elapsed = perf_counter() - start
        timings.append(elapsed)

    median_seconds = float(np.median(timings))

    predict_ms_per_1000 = (
        median_seconds
        * 1000.0
        * 1000.0
        / len(predict_profiles)
    )

    model_bytes = len(
        pickle.dumps(
            pipeline,
            protocol=pickle.HIGHEST_PROTOCOL,
        )
    )

    return {
        "fit_seconds": float(fit_seconds),
        "predict_ms_per_1000": float(
            predict_ms_per_1000
        ),
        "model_bytes": int(model_bytes),
    }

def fit_p3_variant(profiles, family, params, seed=C.SEED):
    """Ajusta una variante de P3 con train y evalúa únicamente validation."""
    periods = ("train", "validation")
    required = set(periods)

    missing = required.difference(profiles)
    if missing:
        raise ValueError(
            f"faltan perfiles requeridos para P3: {sorted(missing)}"
        )

    pipeline = build_p3_pipeline(
        family,
        params,
        seed=seed,
    )

    fit_start = perf_counter()
    pipeline.fit(profiles["train"])
    fit_seconds = perf_counter() - fit_start

    model = pipeline.named_steps["model"]
    if hasattr(model, "converged_") and not model.converged_:
        raise RuntimeError(
            "GMM no convergió; la variante no puede considerarse terminada."
        )

    scaler = pipeline.named_steps["scaler"]

    scaled = {
        split: scaler.transform(profiles[split])
        for split in periods
    }

    labels = {
        split: pipeline.predict(profiles[split])
        for split in periods
    }

    metrics = {}

    for split, prefix in (
        ("train", "train"),
        ("validation", "val"),
    ):
        metrics.update(
            cluster_metrics(
                scaled[split],
                labels[split],
                prefix,
            )
        )

    metrics.update(
        p3_model_cost_metrics(
            pipeline,
            profiles["validation"],
            fit_seconds,
        )
    )

    return {
        "pipeline": pipeline,
        "labels": labels,
        "metrics": metrics,
        "scaled": scaled,
    }

def evaluate_p3_test(pipeline, test_profiles):
    """Evalúa un pipeline P3 ya entrenado sobre el periodo de prueba."""
    if len(test_profiles) == 0:
        raise ValueError(
            "test_profiles no puede estar vacío"
        )

    scaler = pipeline.named_steps["scaler"]

    scaled_test = scaler.transform(test_profiles)
    labels_test = pipeline.predict(test_profiles)

    metrics = cluster_metrics(
        scaled_test,
        labels_test,
        "test",
    )

    return {
        "labels": labels_test,
        "metrics": metrics,
        "scaled": scaled_test,
    }

def p3_stability_scores(
    train_frame,
    station_ids,
    train_profiles,
    reference_labels,
    family,
    params,
    seed=C.SEED,
    n_bootstraps=C.P3_BOOTSTRAPS,
):
    """Evalúa estabilidad con remuestreos de días completos de train."""
    required_columns = {"station_id", "prediction_time", "departures"}
    missing_columns = required_columns.difference(train_frame.columns)
    if missing_columns:
        raise ValueError(
            f"faltan columnas requeridas para estabilidad P3: "
            f"{sorted(missing_columns)}"
        )

    if n_bootstraps < 1:
        raise ValueError("n_bootstraps debe ser al menos 1")

    reference_labels = np.asarray(reference_labels)
    if len(reference_labels) != len(station_ids):
        raise ValueError(
            "reference_labels debe contener una asignación por estación"
        )

    dates = pd.to_datetime(
        train_frame["prediction_time"]
    ).dt.normalize()

    days = pd.Index(dates.drop_duplicates())

    if len(days) == 0:
        raise ValueError(
            "no hay días de entrenamiento disponibles para estabilidad"
        )

    rng = np.random.default_rng(seed)
    scores = []

    for i in range(n_bootstraps):
        sampled_days = pd.Series(
            pd.to_datetime(
                rng.choice(
                    days.to_numpy(),
                    size=len(days),
                    replace=True,
                )
            )
        )

        multiplicity = sampled_days.value_counts()

        weighted = train_frame.copy()
        weighted["sample_weight"] = (
            dates.map(multiplicity).fillna(0).to_numpy()
        )

        bootstrap_profiles = station_usage_profiles(
            weighted,
            station_ids,
            weight="sample_weight",
        )

        pipeline = build_p3_pipeline(
            family,
            params,
            seed=seed + i + 1,
        )

        pipeline.fit(bootstrap_profiles)

        model = pipeline.named_steps["model"]
        if hasattr(model, "converged_") and not model.converged_:
            raise RuntimeError(
                "GMM no convergió durante la evaluación de estabilidad."
            )

        bootstrap_labels = pipeline.predict(train_profiles)

        scores.append(
            float(
                adjusted_rand_score(
                    reference_labels,
                    bootstrap_labels,
                )
            )
        )

    return scores

def build_p3_artifacts(
    train_profiles,
    station_ids,
    labels,
    stations,
    output_dir,
):
    """Genera tablas y figuras interpretables para una variante de P3."""
    from pathlib import Path

    labels = np.asarray(labels)

    if len(labels) != len(station_ids):
        raise ValueError(
            "labels debe contener una asignación por estación"
        )

    if len(train_profiles) != len(station_ids):
        raise ValueError(
            "train_profiles debe contener una fila por estación"
        )

    required_station_columns = {
        "station_id",
        "station_name",
        "latitude",
        "longitude",
    }
    missing = required_station_columns.difference(stations.columns)
    if missing:
        raise ValueError(
            f"faltan columnas del catálogo de estaciones: {sorted(missing)}"
        )

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    assignments = pd.DataFrame(
        {
            "station_id": [str(value) for value in station_ids],
            "cluster": labels,
        }
    )

    station_catalog = stations[
        [
            "station_id",
            "station_name",
            "latitude",
            "longitude",
        ]
    ].copy()

    station_catalog["station_id"] = (
        station_catalog["station_id"].astype(str)
    )

    assignments = assignments.merge(
        station_catalog,
        on="station_id",
        how="left",
        validate="one_to_one",
    )

    profiles = train_profiles.copy()
    profiles["cluster"] = labels

    profiles_by_cluster = (
        profiles
        .groupby("cluster", observed=True)
        .mean(numeric_only=True)
        .sort_index()
    )

    profiles_path = output_dir / "perfiles_grupos.png"

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(10, 4),
    )

    for cluster, row in profiles_by_cluster.iterrows():
        axes[0].plot(
            range(24),
            row.iloc[:24],
            label=f"Grupo {cluster}",
        )

        axes[1].plot(
            range(24),
            row.iloc[24:48],
            label=f"Grupo {cluster}",
        )

    axes[0].set(
        title="Días laborales",
        xlabel="Hora",
        ylabel="Proporción media de salidas",
    )

    axes[1].set(
        title="Fin de semana",
        xlabel="Hora",
        ylabel="Proporción media de salidas",
    )

    for ax in axes:
        ax.legend()

    fig.suptitle(
        "P3 — perfiles horarios por grupo (train)"
    )

    fig.savefig(
        profiles_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    location_path = output_dir / "ubicacion_grupos.png"

    fig, ax = plt.subplots(figsize=(7, 6))

    valid = (
        assignments["latitude"].notna()
        & assignments["longitude"].notna()
    )

    for cluster, group in assignments.loc[valid].groupby(
        "cluster",
        observed=True,
    ):
        ax.scatter(
            group["longitude"],
            group["latitude"],
            s=18,
            alpha=0.8,
            label=f"Grupo {cluster} (n={len(group)})",
        )

    ax.set(
        xlabel="Longitud",
        ylabel="Latitud",
        title="P3 — ubicación de estaciones por grupo",
    )

    ax.legend()

    if valid.any():
        mean_latitude = assignments.loc[
            valid,
            "latitude",
        ].mean()

        ax.set_aspect(
            1 / np.cos(np.radians(mean_latitude))
        )

    fig.savefig(
        location_path,
        dpi=150,
        bbox_inches="tight",
    )
    plt.close(fig)

    return {
        "assignments": assignments,
        "profiles_by_cluster": profiles_by_cluster,
        "plots": {
            "perfiles_grupos": profiles_path,
            "ubicacion_grupos": location_path,
        },
    }

def make_model(role, seed=C.SEED):
    if role == "baseline":
        return KMeans(**{**C.P3_KMEANS_PARAMS, "random_state": seed})
    return GaussianMixture(**{**C.P3_GMM_PARAMS, "random_state": seed})


def cluster_metrics(X, labels, prefix):
    """Devuelve métricas solo cuando son definibles; no inventa puntuaciones para un grupo."""
    counts = pd.Series(labels).value_counts()
    metrics = {f"{prefix}_n_clusters": len(counts),
               f"{prefix}_min_cluster_size": int(counts.min()),
               f"{prefix}_min_cluster_share": float(counts.min() / len(labels))}
    if 1 < len(counts) < len(labels):
        metrics[f"{prefix}_silhouette"] = float(silhouette_score(X, labels))
        metrics[f"{prefix}_davies_bouldin"] = float(davies_bouldin_score(X, labels))
    return metrics


class P3Experiment:
    """Compara KMeans y GMM con perfiles horarios y un escalador ajustado en train.

    Las coordenadas se unen después de agrupar. La selección usa silhouette de validación
    con grupos de train de al menos 5%; prueba no interviene en el ajuste ni la selección.
    """
    def __init__(self, metadata, X, y, stations):
        self.metadata = metadata
        train = metadata["split"].eq("train")
        totals = y.loc[train].groupby(metadata.loc[train, "station_id"], observed=True).sum()
        self.station_ids = sorted(totals[totals.ge(C.P3_MIN_TRAIN_TRIPS)].index.astype(str))
        if len(self.station_ids) <= C.P3_K:
            raise ValueError("P3 requiere más estaciones elegibles que grupos.")
        self.frame = metadata[["station_id", "prediction_time", "split"]].copy()
        self.frame["departures"] = y.to_numpy()
        self.profiles = {name: station_usage_profiles(
            self.frame.loc[self.frame["split"].eq(name)], self.station_ids)
            for name in ("train", "validation", "test")}
        self.stations = stations

    def stability(self, role, labels):
        """ARI sobre cinco remuestreos de días completos de train con reemplazo."""
        frame = self.frame.loc[self.frame["split"].eq("train")].copy()
        dates = frame["prediction_time"].dt.normalize()
        days = dates.unique()
        rng = np.random.default_rng(C.SEED)
        scores = []
        for i in range(C.P3_BOOTSTRAPS):
            multiplicity = pd.Series(rng.choice(days, len(days), replace=True)).value_counts()
            weighted = frame.copy()
            weighted["sample_weight"] = dates.map(multiplicity).fillna(0).to_numpy()
            profile = station_usage_profiles(weighted, self.station_ids, weight="sample_weight")
            sampled = self.scaler.transform(profile)
            resampled_model = make_model(role, C.SEED + i + 1).fit(sampled)
            scores.append(float(adjusted_rand_score(labels, resampled_model.predict(self.scaled["train"]))))
        return scores

    def fit(self):
        self.scaler = StandardScaler().fit(
            self.profiles["train"]
        )

        periods = ("train", "validation")

        self.scaled = {
            name: self.scaler.transform(self.profiles[name])
            for name in periods
        }

        self.models = {}
        self.labels = {}
        self.metrics = {}
        self.bootstrap_scores = {}

        for role in ("baseline", "candidato"):
            model = make_model(role).fit(
                self.scaled["train"]
            )

            if (
                hasattr(model, "converged_")
                and not model.converged_
            ):
                raise RuntimeError(
                    "GMM no convergió; no se registra "
                    "como experimento terminado."
                )

            self.models[role] = model

            self.labels[role] = {
                name: model.predict(self.scaled[name])
                for name in periods
            }

            metrics = {}

            for name, prefix in (
                ("train", "train"),
                ("validation", "val"),
            ):
                metrics.update(
                    cluster_metrics(
                        self.scaled[name],
                        self.labels[role][name],
                        prefix,
                    )
                )

            stability = self.stability(
                role,
                self.labels[role]["train"],
            )

            self.bootstrap_scores[role] = stability

            metrics["train_stability_ari_mean"] = float(
                np.mean(stability)
            )
            metrics["train_stability_ari_min"] = float(
                np.min(stability)
            )

            self.metrics[role] = metrics

        eligible = {
            role: metrics
            for role, metrics in self.metrics.items()
            if (
                metrics.get(
                    "train_min_cluster_share",
                    0,
                )
                >= C.P3_MIN_CLUSTER_SHARE
                and "val_silhouette" in metrics
            )
        }

        self.selected = (
            max(
                eligible,
                key=lambda role: eligible[role][
                    "val_silhouette"
                ],
            )
            if eligible
            else "ninguno"
        )

        return self

    def evaluate_test(self):
        """Evalúa test después de haber congelado la selección."""
        if not hasattr(self, "selected"):
            raise RuntimeError(
                "Debe ejecutarse fit antes de evaluar test."
            )

        if self.selected == "ninguno":
            raise RuntimeError(
                "No existe una selección válida; "
                "test permanece reservado."
            )

        scaled_test = self.scaler.transform(
            self.profiles["test"]
        )

        self.scaled["test"] = scaled_test

        for role in ("baseline", "candidato"):
            labels_test = self.models[role].predict(
                scaled_test
            )

            self.labels[role]["test"] = labels_test

            self.metrics[role].update(
                cluster_metrics(
                    scaled_test,
                    labels_test,
                    "test",
                )
            )

        return self

    def artifacts(self, role):
        labels = self.labels[role]["train"]
        assignment = pd.DataFrame({"station_id": self.station_ids, "cluster": labels})
        assignment = assignment.merge(self.stations[["station_id", "station_name", "latitude", "longitude"]],
                                      on="station_id", how="left", validate="one_to_one")
        profiles = self.profiles["train"].assign(cluster=labels).groupby("cluster").mean()
        figures = []
        C.FIGURES.mkdir(parents=True, exist_ok=True)
        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        for cluster, row in profiles.iterrows():
            axes[0].plot(range(24), row.iloc[:24], label=f"Grupo {cluster}")
            axes[1].plot(range(24), row.iloc[24:], label=f"Grupo {cluster}")
        for ax, title in zip(axes, ["Días laborales", "Fin de semana"]):
            ax.set(title=title, xlabel="Hora", ylabel="Proporción media de salidas")
            ax.legend()
        fig.suptitle(f"P3 perfiles de entrenamiento {role}")
        path = C.FIGURES / f"p3_perfiles_{role}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig); figures.append(path)
        fig, ax = plt.subplots(figsize=(7, 6))
        valid = assignment["latitude"].notna() & assignment["longitude"].notna()
        for cluster, group in assignment.loc[valid].groupby("cluster"):
            ax.scatter(group.longitude, group.latitude, s=18, alpha=.8, label=f"Grupo {cluster} (n={len(group)})")
        ax.set(xlabel="Longitud", ylabel="Latitud", title=f"P3 estaciones por grupo {role}")
        ax.legend(); ax.set_aspect(1 / np.cos(np.radians(20.67)))
        path = C.FIGURES / f"p3_mapa_{role}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig); figures.append(path)
        return assignment, profiles, figures

    def log(self, executor):
        for role in ("baseline", "candidato"):
            assignment, profiles, figures = self.artifacts(role)
            params = {**common_params(self.metadata), "model": type(self.models[role]).__name__,
                      "horizon_minutes": 0, "horizon": "historical_profiles",
                      "profile_features": 48, "normalization": "mean_per_hour_then_L1_per_day_type",
                      "scaler": "StandardScaler_fit_train", "min_train_trips": C.P3_MIN_TRAIN_TRIPS,
                      "bootstrap_train_days": C.P3_BOOTSTRAPS, "selected_model": self.selected,
                      "min_cluster_share": C.P3_MIN_CLUSTER_SHARE,
                      **(C.P3_KMEANS_PARAMS if role == "baseline" else C.P3_GMM_PARAMS)}
            params["n_stations"] = len(self.station_ids)
            tags = {**common_tags("P3", "clustering", executor, "persona1",
                                "perfiles históricos estación-hora por tipo de día"),
                    "model_role": role, "selected": str(role == self.selected).lower()}
            notes = ("Selección: mayor val_silhouette con train_min_cluster_share >= 0.05. "
                     "k=3 fijado antes de prueba. Train usa octubre-mayo; test no ajusta el modelo. "
                     "El mapa usa coordenadas del catálogo de septiembre y no incluye base cartográfica. "
                     "Las asignaciones son descriptivas y no prueban causas ni impacto urbano.")
            log_model_run(f"P3-{role}-{type(self.models[role]).__name__}", tags, params,
                          self.metrics[role], {"metrics.json": json.dumps(self.metrics[role], indent=2),
                          "estaciones_por_grupo.csv": assignment.to_csv(index=False),
                          "perfiles_por_grupo.csv": profiles.to_csv(),
                          "stability_ari.json": json.dumps(self.bootstrap_scores[role]),
                          "evaluation_notes.txt": notes}, figures)


def main():
    parser = argparse.ArgumentParser(description="P3: grupos de patrones de uso de estaciones")
    parser.add_argument("--executor", default=os.environ.get("MIBICI_EXECUTOR", "persona1"))
    args = parser.parse_args()
    exp = P3Experiment(
        *load_tables(),
        pd.read_parquet(C.PROCESSED / "stations.parquet"),
    ).fit()

    exp.evaluate_test()

    exp.log(args.executor)

    print(
        json.dumps(
            {
                "selected": exp.selected,
                "metrics": exp.metrics,
            },
            indent=2,
        )
    )

if __name__ == "__main__":
    main()
