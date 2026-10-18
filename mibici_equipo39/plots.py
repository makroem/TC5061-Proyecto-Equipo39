import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def p1_error_by_hour(frame, predictions, path):
    fig, ax = plt.subplots(figsize=(8, 4))
    for name, pred in predictions.items():
        error = (frame["y"] - pred).abs().groupby(frame["hour_of_day"]).mean()
        ax.plot(error.index, error.values, marker="o", label=name)
    ax.set(xlabel="Hora del día", ylabel="MAE (viajes por estación)", title="P1: error en prueba por hora")
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
    ax.set(xlabel="Hora", ylabel="Salidas", title=f"P1: estación {station}, primeras horas de prueba")
    ax.legend()
    fig.autofmt_xdate()
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return path
