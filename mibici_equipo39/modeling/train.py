import argparse
import os

from mibici_equipo39 import config as C
from mibici_equipo39.features import load_p2_targets, load_tables
from mibici_equipo39.modeling.p1 import P1Experiment
from mibici_equipo39.modeling.p2 import P2Experiment
from mibici_equipo39.modeling.tracking import git_state

QUESTIONS = ("P1", "P2")
REQUIRED = [
    C.REFERENCES / "data_manifest.json",
    C.REFERENCES / "split_manifest.json",
    C.PROCESSED / "metadata.parquet",
    C.PROCESSED / "X_p1.parquet",
    C.PROCESSED / "y_p1.parquet",
    C.PROCESSED / "y_p2.parquet",
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
        raise SystemExit("Hay cambios sin commit; los runs finales deben quedar ligados a un commit. Usa --allow-dirty solo para pruebas.")


def run(questions, member):
    metadata, X, y = load_tables()
    results = {}
    if "P1" in questions:
        experiment = P1Experiment(metadata, X, y).fit()
        experiment.log(member)
        results["P1"] = experiment
    if "P2" in questions:
        experiment = P2Experiment(metadata, X, load_p2_targets()).fit()
        experiment.log(member)
        results["P2"] = experiment
    for question, experiment in results.items():
        print(question, "seleccionado:", experiment.selected)
    return results


def main():
    parser = argparse.ArgumentParser(description="Controlador común de experimentos MiBici")
    parser.add_argument("--question", choices=[*QUESTIONS, "all"], default="all")
    parser.add_argument("--member", choices=["persona1", "persona2", "persona3", "persona4"],
                        default=os.environ.get("MIBICI_EXECUTOR", "persona1"))
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    check_inputs(args.allow_dirty)
    run(QUESTIONS if args.question == "all" else (args.question,), args.member)


if __name__ == "__main__":
    main()
