import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import precision_recall_curve


def p1_error_by_hour(frame, predictions, path):
    fig, ax = plt.subplots(figsize=(8, 4))
    for name, pred in predictions.items():
        error = (frame["y"] - pred).abs().groupby(frame["hour_of_day"]).mean()
        ax.plot(error.index, error.values, marker="o", label=name)
    ax.set(
        xlabel="Hora del día",
        ylabel="MAE (viajes por estación)",
        title="P1: error en prueba por hora",
    )
    ax.legend()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def p2_precision_recall(frame, scores, targets, path, min_recall=0.80):
    val = frame["split"].eq("validation").to_numpy()
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, (name, target) in zip(axes, targets.items()):
        y = frame[target].to_numpy()[val]
        for model, by_target in scores.items():
            precision, recall, _ = precision_recall_curve(y, by_target[name][val])
            ax.plot(recall, precision, label=model)
        ax.axvline(min_recall, color="grey", linestyle="--", linewidth=1)
        ax.set(
            title=f"P2 riesgo aproximado {name} (validación)",
            xlabel="recall",
            ylabel="precisión",
            ylim=(0, 0.6),
        )
        ax.legend()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def p1_station_week(frame, predictions, path):
    station = frame.groupby("station_id", observed=True)["y"].sum().idxmax()
    week = frame.loc[frame["station_id"].eq(station)].sort_values("prediction_time").head(24 * 7)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(week["prediction_time"], week["y"], color="black", label="real")
    for name, pred in predictions.items():
        ax.plot(week["prediction_time"], pred[week.index], label=name, alpha=0.8)
    ax.set(
        xlabel="Hora", ylabel="Salidas", title=f"P1: estación {station}, primeras horas de prueba"
    )
    ax.legend()
    fig.autofmt_xdate()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path

def p1_real_vs_predicho(y_true, y_pred, path):
    fig, ax = plt.subplots(figsize=(6, 6))

    ax.scatter(
        y_true,
        y_pred,
        alpha=0.3,
        s=10,
    )

    low = min(y_true.min(), y_pred.min())
    high = max(y_true.max(), y_pred.max())

    ax.plot(
        [low, high],
        [low, high],
        color="red",
        linestyle="--",
    )

    ax.set(
        xlabel="Viajes reales por estación y hora",
        ylabel="Viajes predichos por estación y hora",
        title="Real vs predicho (prueba)",
    )

    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return path

def p1_residuales(y_true, y_pred, path):
    residuals = y_true - y_pred

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.scatter(
        y_pred,
        residuals,
        alpha=0.3,
        s=10,
    )

    ax.axhline(
        0,
        color="red",
        linestyle="--",
    )

    ax.set(
        xlabel="Viajes predichos por estación y hora",
        ylabel="Residual",
        title="Residuales (prueba)",
    )

    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)

    return path