"""Comparación pareada; el remuestreo conserva todas las estaciones de cada día."""

import numpy as np
import pandas as pd


def metrics(y, prediction):
    y, prediction = np.asarray(y, dtype=float), np.asarray(prediction, dtype=float)
    if y.ndim != 1 or prediction.shape != y.shape or not len(y):
        raise ValueError("Se requieren vectores alineados y no vacíos.")
    if not np.isfinite(y).all() or not np.isfinite(prediction).all():
        raise ValueError("No se admiten predicciones ni objetivos no finitos.")
    return {"mae": float(np.mean(np.abs(prediction-y))), "rmse": float(np.sqrt(np.mean((prediction-y)**2)))}


def improvement(baseline, candidate):
    return None if baseline == 0 else 100 * (baseline-candidate) / baseline


def block_bootstrap(dates, y, a, b, block_days=7, repeats=1000, seed=39):
    """IC exploratorio de MAE(B)-MAE(A), con bloques móviles de días consecutivos."""
    metrics(y, a)
    metrics(y, b)
    frame = pd.DataFrame({"day": pd.DatetimeIndex(pd.to_datetime(dates)).normalize(),
                          "delta": np.abs(np.asarray(b)-np.asarray(y)) - np.abs(np.asarray(a)-np.asarray(y))})
    daily = frame.groupby("day").delta.agg(["sum", "size"]).sort_index()
    n = len(daily)
    if block_days < 1 or n < block_days or repeats < 1:
        raise ValueError("La longitud del bloque y las repeticiones deben ser válidas.")
    if not pd.date_range(daily.index.min(), daily.index.max(), freq="D").equals(daily.index):
        raise ValueError("Los días del remuestreo deben ser consecutivos.")
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        starts = rng.integers(0, n-block_days+1, size=int(np.ceil(n/block_days)))
        indices = (starts[:, None] + np.arange(block_days)).ravel()[:n]
        sampled = daily.iloc[indices]
        values.append(float(sampled["sum"].sum()/sampled["size"].sum()))
    lower, upper = np.quantile(values, [0.025, 0.975])
    return {"delta_mae_b_minus_a": float(daily["sum"].sum()/daily["size"].sum()),
            "ci95_low": float(lower), "ci95_high": float(upper), "block_days": block_days,
            "days": n, "repeats": repeats, "seed": seed,
            "interpretation": "Intervalo exploratorio: un mes contiene pocos ciclos semanales; no demuestra un efecto causal."}
