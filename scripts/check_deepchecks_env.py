"""Comprueba DeepChecks con datos sintéticos; no valida los datos del proyecto."""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path

# Evitar la consulta de versiones durante la comprobación de compatibilidad.
os.environ["DISABLE_LATEST_VERSION_CHECK"] = "True"

import pandas as pd
from deepchecks.tabular import Dataset, Suite
from deepchecks.tabular.checks import IsSingleValue


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("private_quality/deepchecks_smoke"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    suite = Suite("Compatibilidad del entorno - datos sinteticos",
                  IsSingleValue().add_condition_not_single_value())
    cases = {"variable": pd.DataFrame({"count": [1, 2, 3, 4]}),
             "constant": pd.DataFrame({"count": [1, 1, 1, 1]})}
    results = {}
    for name, frame in cases.items():
        result = suite.run(Dataset(frame, cat_features=[]))
        path = args.output / (name + ".html")
        result.save_as_html(str(path), as_widget=False, connected=False)
        passed = result.passed(fail_if_check_not_run=True)
        if passed != (name == "variable"):
            raise RuntimeError(f"Resultado inesperado para el caso sintético {name}")
        results[name] = {"condition_passed": bool(passed), "html": path.name,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    summary = {"scope": "compatibilidad con datos sinteticos; no valida CSV reales",
               "status": "PASS", "cases": results,
               "versions": {name: importlib.metadata.version(name) for name in
                            ["deepchecks", "numpy", "pandas", "scikit-learn", "plotly", "ipython"]}}
    (args.output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
