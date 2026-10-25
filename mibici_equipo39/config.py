"""Parámetros compartidos de descarga, partición y experimentos."""

import os
from pathlib import Path

ROOT = Path(os.environ.get("MIBICI_PROJECT_ROOT", Path(__file__).resolve().parents[1]))
DATA = ROOT / "data"
RAW = DATA / "raw"
EXTERNAL = DATA / "external"
PROCESSED = DATA / "processed"
INTERIM = DATA / "interim"
REFERENCES = ROOT / "references"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures" / "runs"
MODELS = ROOT / "models"
TEAM = "39"
SEED = 39
SOURCE_START = "2025-10-01"
SOURCE_END_EXCLUSIVE = "2026-10-01"
TIMEZONE = "America/Mexico_City"
CHUNKSIZE = 100000
TRAIN_END_EXCLUSIVE = "2026-06-01"
VALIDATION_END_EXCLUSIVE = "2026-08-01"
SPLIT_STRATEGY = "chronological_holdout"
SPLIT_VERSION = "3"
CLEANING_SCHEMA_VERSION = "3-colab"
FEATURE_SCHEMA_VERSION = "6-chronological-calendar-only"
FEATURES_START = SOURCE_START
P1_MIN_TRAIN_DEPARTURES = 100
P1_HGB_100_PARAMS = {
    "loss": "poisson",
    "learning_rate": 0.1,
    "max_iter": 100,
    "max_leaf_nodes": 31,
    "random_state": SEED,
}

P1_HGB_200_PARAMS = {
    "loss": "poisson",
    "learning_rate": 0.05,
    "max_iter": 200,
    "max_leaf_nodes": 31,
    "random_state": SEED,
}

P1_RF_300_PARAMS = {
    "n_estimators": 300,
    "max_depth": 16,
    "min_samples_leaf":20,
    "max_samples": 0.5,
    "bootstrap": True,
    "n_jobs": 2,
    "random_state": SEED,
}

P2_INITIAL_OCCUPANCY, P2_MARGIN = 0.50, 0.10
P2_SENSITIVITY_OCCUPANCIES = (0.25, 0.75)
P2_MIN_RECALL = 0.80
P2_THRESHOLDS = tuple(round(0.05 * i, 2) for i in range(1, 20))
P2_LOGISTIC_PARAMS = {
    "C": 1.0,
    "class_weight": "balanced",
    "solver": "liblinear",
    "max_iter": 1000,
    "random_state": SEED,
}
P3_K, P3_MIN_TRAIN_TRIPS = 3, 100
P3_BOOTSTRAPS = 5
P3_MIN_CLUSTER_SHARE = 0.05
P3_KMEANS_PARAMS = {"n_clusters": P3_K, "n_init": 20, "random_state": SEED}
P3_GMM_PARAMS = {"n_components": P3_K, "covariance_type": "diag", "reg_covar": 1e-6,
                 "n_init": 5, "max_iter": 300, "random_state": SEED}
EXPERIMENT_NAME = "mibici-equipo39"
TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
REGISTRY_URI = os.environ.get("MLFLOW_REGISTRY_URI", TRACKING_URI)
# Los resultados de la segunda entrega pueden guardarse fuera del clon.
RESULTS_DIR = Path(os.environ.get("MIBICI_RESULTS_DIR", ROOT / "private_results"))
MODEL_ALIAS = "champion"
REGISTERED_MODELS = {
    "p1": "mibici-equipo39-p1-demanda",
    "p2": "mibici-equipo39-p2-riesgo",
    "p3": "mibici-equipo39-p3-grupos",
}
STAGE2_SEARCH_PLAN = {
    "p1": [
        {"name": "p1_hgb_100", "family": "hgb", "params": dict(P1_HGB_100_PARAMS)},
        {"name": "p1_hgb_200", "family": "hgb", "params": {
            **P1_HGB_200_PARAMS, "max_iter": 200, "learning_rate": 0.05}},
        {"name": "p1_rf_300", "family": "random_forest", "params": {
            "n_estimators": 300, "max_depth": 16, "min_samples_leaf": 20,
            "max_samples": 0.5, "bootstrap": True, "n_jobs": 2, "random_state": SEED}},
    ],
    "p2": [
        {"name": f"p2_lr_{value:g}", "family": "logistic", "params": {
            **P2_LOGISTIC_PARAMS, "C": value}} for value in (0.1, 1.0, 10.0)
    ],
    "p3": [
        {"name": "p3_kmeans_4", "family": "kmeans", "params": {
            **P3_KMEANS_PARAMS, "n_clusters": 4}},
        {"name": "p3_kmeans_5", "family": "kmeans", "params": {
            **P3_KMEANS_PARAMS, "n_clusters": 5}},
        {"name": "p3_gmm_3", "family": "gmm", "params": dict(P3_GMM_PARAMS)},
    ],
}
SOURCE_URLS = {
    "2025-10": "https://mibici.net/site/assets/files/115104/datos_abiertos_2025_10.csv",
    "2025-11": "https://mibici.net/site/assets/files/116773/datos_abiertos_2025_11.csv",
    "2025-12": "https://mibici.net/site/assets/files/118153/datos_abiertos_2025_12.csv",
    "2026-01": "https://mibici.net/site/assets/files/120163/datos_abiertos_2026_01.csv",
    "2026-02": "https://mibici.net/site/assets/files/121761/datos_abiertos_2026_02.csv",
    "2026-03": "https://mibici.net/site/assets/files/123236/datos_abiertos_2026_03.csv",
    "2026-04": "https://mibici.net/site/assets/files/124927/datos_abiertos_2026_04.csv",
    "2026-05": "https://mibici.net/site/assets/files/125943/datos_abiertos_2026_05.csv",
    "2026-06": "https://mibici.net/site/assets/files/127734/datos_abiertos_2026_06.csv",
    "2026-07": "https://mibici.net/site/assets/files/129006/datos_abiertos_2026_07.csv",
    "2026-08": "https://mibici.net/site/assets/files/130362/datos_abiertos_2026_08.csv",
    "2026-09": "https://mibici.net/site/assets/files/131825/datos_abiertos_2026_09.csv",
}
STATIONS_URL = "https://mibici.net/site/assets/files/1118/nomenclatura_2026_09.csv"
