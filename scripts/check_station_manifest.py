"""Compara el catalogo de estaciones con su manifiesto sin modificar los datos.

El resumen contiene conteos y hashes por columna, sin filas del catalogo.
Ejecutar en los dos equipos con el mismo commit y comparar los JSON.
"""

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import pyarrow as pa

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D


def value_hash(series):
    """Distingue diferencias de valores de diferencias al representarlos en CSV."""
    values = []
    for value in series.tolist():
        if pd.isna(value):
            values.append(None)
        elif isinstance(value, (float, np.floating)):
            values.append({"float_hex": float(value).hex()})
        elif isinstance(value, (bool, np.bool_)):
            values.append(bool(value))
        elif isinstance(value, (int, np.integer)):
            values.append(int(value))
        else:
            values.append(str(value))
    return hashlib.sha256(D.canonical(values).encode("utf-8")).hexdigest()


def table_summary(frame):
    ordered = frame.sort_values("station_id").reset_index(drop=True)
    return {
        "rows": len(ordered),
        "logical_sha256": D.logical_hash(ordered, ["station_id"]),
        "columns": {
            name: {
                "dtype": str(ordered[name].dtype),
                "nulls": int(ordered[name].isna().sum()),
                "csv_sha256": D.logical_hash(
                    ordered[list(dict.fromkeys(["station_id", name]))], ["station_id"]
                ),
                "values_sha256": value_hash(ordered[name]),
            }
            for name in ordered
        },
        "names_with_outer_spaces": int(
            ordered.station_name.ne(ordered.station_name.str.strip()).sum()
        ),
    }


def inspect(project_root, verify_outputs=False):
    """Verifica fuentes, valores y salidas; nunca regenera datos ni manifiestos."""
    manifest_path = project_root / "references/data_manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    source_name = Path(C.STATIONS_URL).name
    source_info = next(s for s in manifest["sources"] if s.get("name") == source_name)
    source_path = project_root / "data/external" / source_name
    parquet_path = project_root / "data/processed/stations.parquet"
    before = {"source": D.sha_file(source_path), "parquet": D.sha_file(parquet_path),
              "manifest": D.sha_file(manifest_path)}
    stored = pd.read_parquet(parquet_path)
    rebuilt, encoding, separator = D.clean_stations(source_path)
    expected = manifest["outputs"]["processed/stations.parquet"]
    tables = {"stored": table_summary(stored), "rebuilt_from_csv": table_summary(rebuilt)}
    checks = {
        "source_sha256_matches": before["source"] == source_info["sha256"],
        "stored_matches_manifest": all(tables["stored"][k] == expected[k]
                                       for k in ("rows", "logical_sha256")),
        "rebuilt_matches_manifest": all(tables["rebuilt_from_csv"][k] == expected[k]
                                        for k in ("rows", "logical_sha256")),
        "stored_equals_rebuilt": stored.equals(rebuilt),
    }
    outputs = {"performed": verify_outputs, "checked": 0, "mismatches": []}
    if verify_outputs:
        for relative, info in manifest["outputs"].items():
            path = project_root / "data" / relative
            outputs["checked"] += 1
            if not path.is_file():
                outputs["mismatches"].append({"file": relative, "reason": "missing"})
                continue
            frame = pd.read_parquet(path)
            keys = ["station_id"] if relative.endswith("stations.parquet") else ["trip_id"]
            found = {"rows": len(frame), "logical_sha256": D.logical_hash(frame, keys)}
            if found != info:
                outputs["mismatches"].append({"file": relative, "expected": info, "found": found})
        checks["all_outputs_match"] = not outputs["mismatches"]
    checks["inputs_unchanged"] = before == {
        "source": D.sha_file(source_path), "parquet": D.sha_file(parquet_path),
        "manifest": D.sha_file(manifest_path),
    }
    return {
        "status": "PASS" if all(checks.values()) else "FAIL",
        "environment": {"os": platform.system(), "machine": platform.machine(),
                        "python": platform.python_version(), "pandas": pd.__version__,
                        "numpy": np.__version__, "pyarrow": pa.__version__},
        "data_version": manifest["data_version"], "expected_stations": expected,
        "source_sha256": before["source"], "parquet_sha256": before["parquet"],
        "manifest_sha256": before["manifest"], "encoding": encoding, "separator": separator,
        "checks": checks, "tables": tables, "outputs": outputs,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=C.ROOT)
    parser.add_argument("--verify-outputs", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError("Usar un archivo de salida nuevo; no se sobrescribe evidencia.")
    result = inspect(args.project_root, args.verify_outputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps({"status": result["status"], "checks": result["checks"],
                      "outputs_checked": result["outputs"]["checked"]}))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
