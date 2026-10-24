import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay, confusion_matrix, precision_recall_curve


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


def p2_confusion_matrices(frame, output, thresholds, path, split_name="validación"):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, risk, target in zip(axes, ("bikes", "docks"), ("y_bikes", "y_docks")):
        matrix = confusion_matrix(frame[target], output[f"alert_{risk}"], labels=[0, 1])
        ConfusionMatrixDisplay(matrix, display_labels=["sin riesgo", "riesgo"]).plot(ax=ax, colorbar=False)
        ax.set_title(f"P2 {risk}, {split_name}, umbral {thresholds[risk]}")
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def p2_risk_pr_curves(frame, output, path, min_recall=0.80, split_name="validación"):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, risk, target in zip(axes, ("bikes", "docks"), ("y_bikes", "y_docks")):
        precision, recall, _ = precision_recall_curve(frame[target], output[f"prob_{risk}"])
        ax.plot(recall, precision)
        ax.axhline(frame[target].mean(), color="grey", linestyle=":", label="prevalencia")
        ax.axvline(min_recall, color="grey", linestyle="--", label="recall mínimo")
        ax.set(title=f"P2 precisión-recall {risk}, {split_name}", xlabel="recall", ylabel="precisión")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path


def p2_threshold_curves(searches, thresholds, path, min_recall=0.80, split_name="validación"):
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, risk in zip(axes, ("bikes", "docks")):
        table = searches[risk]
        grid = [row["threshold"] for row in table]
        ax.plot(grid, [row["recall"] for row in table], marker="o", label="recall")
        ax.plot(grid, [row["precision"] for row in table], marker="o", label="precisión")
        ax.axhline(min_recall, color="grey", linestyle=":", label="recall mínimo")
        ax.axvline(thresholds[risk], color="black", linestyle="--", label=f"umbral {thresholds[risk]}")
        ax.set(title=f"P2 selección de umbral {risk}, {split_name}", xlabel="umbral", ylabel="valor")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
