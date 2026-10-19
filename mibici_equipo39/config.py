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
FIGURES = REPORTS / "figures"
MODELS = ROOT / "models"
TEAM = "39"
SEED = 39
SOURCE_START = "2025-10-01"
SOURCE_END_EXCLUSIVE = "2026-10-01"
TIMEZONE = "America/Mexico_City"
CHUNKSIZE = 100000
TRAIN_SIZE, VAL_SIZE, TEST_SIZE = 0.70, 0.15, 0.15
SPLIT_STRATEGY = "random_days_month_stratified"
SPLIT_VERSION = "2"
CLEANING_SCHEMA_VERSION = "3-colab"
FEATURE_SCHEMA_VERSION = "5-random-calendar-only"
# Se conserva el inicio del manifiesto confirmado para no cambiar la evaluación.
FEATURES_START = "2025-10-09"
P1_MIN_TRAIN_DEPARTURES = 100
P1_HGB_PARAMS = {
    "loss": "poisson",
    "learning_rate": 0.1,
    "max_iter": 100,
    "max_leaf_nodes": 31,
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
EXPERIMENT_NAME = "mibici-equipo39"
TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db")
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
