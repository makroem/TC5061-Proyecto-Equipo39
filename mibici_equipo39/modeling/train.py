import argparse
import os
import gc
import json

from mibici_equipo39 import config as C
from mibici_equipo39.features import load_p2_targets, load_tables
from mibici_equipo39.modeling.p1 import P1Experiment
from mibici_equipo39.modeling.p2 import P2Experiment
from mibici_equipo39.modeling.p3 import P3Experiment
import pandas as pd
from mibici_equipo39.modeling.tracking import git_state

QUESTIONS = ("P1", "P2", "P3")
REQUIRED = [
    C.REFERENCES / "data_manifest.json",
    C.REFERENCES / "split_manifest.json",
    C.PROCESSED / "metadata.parquet",
    C.PROCESSED / "X_p1.parquet",
    C.PROCESSED / "y_p1.parquet",
    C.PROCESSED / "y_p2.parquet",
    C.PROCESSED / "stations.parquet",
]


def check_inputs(allow_dirty):
    missing = [str(p.relative_to(C.ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        raise SystemExit(
            f"Faltan {missing}. Corre primero python -m mibici_equipo39.dataset --verify-manifest "
            "y python -m mibici_equipo39.features."
        )
    _, dirty = git_state()
    if dirty and not allow_dirty:
        raise SystemExit(
            "Hay cambios sin commit; los runs finales deben quedar ligados a un commit. Usa --allow-dirty solo para pruebas."
        )


def run(questions, member):
    metadata, X, y = load_tables()
    results = {}
    for question in questions:
        if question == "P1":
            experiment = P1Experiment(metadata, X, y).fit()
        elif question == "P2":
            experiment = P2Experiment(metadata, X, load_p2_targets()).fit()
        elif question == "P3":
            experiment = P3Experiment(metadata, X, y, pd.read_parquet(C.PROCESSED / "stations.parquet")).fit()
        else:
            raise ValueError(f"Pregunta desconocida: {question}")
        experiment.log(member)
        print(question, "seleccionado:", experiment.selected)
        results[question] = {"selected": experiment.selected, "metrics": experiment.metrics}
        del experiment
        gc.collect()
    # El resumen se crea después de cerrar todos los runs para conservar git_dirty=false.
    C.REPORTS.mkdir(parents=True, exist_ok=True)
    (C.REPORTS / "experiment_summary.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main():
    parser = argparse.ArgumentParser(description="Controlador común de experimentos MiBici")
    parser.add_argument("--question", choices=[*QUESTIONS, "all"], default="all")
    parser.add_argument(
        "--member",
        choices=["persona1", "persona2", "persona3", "persona4"],
        default=os.environ.get("MIBICI_EXECUTOR", "persona1"),
    )
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    check_inputs(args.allow_dirty)
    run(QUESTIONS if args.question == "all" else (args.question,), args.member)


if __name__ == "__main__":
    main()
