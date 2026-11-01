"""Explica por qué el hash del catálogo cambia entre x86-64 y ARM; no modifica datos.

pandas convierte el texto acumulando number * 10 + dígito. Con FMA esa operación redondea una
vez; sin FMA redondea dos. Se emulan ambas y se comparan con el resultado local y con el manifiesto.
"""

import argparse
from fractions import Fraction
import json
from pathlib import Path
import platform
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D

MAX_DIGITS = 17


def step(number, digit, single_rounding):
    if single_rounding:
        return float(Fraction(number) * 10 + digit)
    return number * 10.0 + digit


def parse(text, single_rounding):
    """Emula precise_xstrtod de pandas para números decimales sin exponente."""
    negative = text.startswith("-")
    whole, _, decimals = text.lstrip("+-").partition(".")
    number, digits, scale = 0.0, 0, 0
    for char in whole:
        if digits < MAX_DIGITS:
            number, digits = step(number, int(char), single_rounding), digits + 1
        else:
            scale += 1
    for char in decimals:
        if digits >= MAX_DIGITS:
            break
        number, digits, scale = step(number, int(char), single_rounding), digits + 1, scale - 1
    number = number / 10.0 ** -scale if scale < 0 else number * 10.0 ** scale
    return -number if negative else number


def emulate(texts, single_rounding):
    return pd.array([parse(t.strip(), single_rounding) if pd.notna(t) else pd.NA for t in texts],
                    dtype="Float64")


def explain(project_root):
    manifest = json.loads((project_root / "references/data_manifest.json").read_text("utf-8"))
    expected = manifest["outputs"]["processed/stations.parquet"]["logical_sha256"]
    source = project_root / "data/external" / Path(C.STATIONS_URL).name
    local, encoding, separator = D.clean_stations(source)
    raw = pd.read_csv(source, encoding=encoding, sep=separator, dtype="string")
    raw.columns = [D.column_name(c) for c in raw.columns]
    raw["station_id"] = raw["id"].str.strip()
    raw = raw.sort_values("station_id").reset_index(drop=True)
    tables, values = {}, {}
    for name, single_rounding in {"un_redondeo": True, "dos_redondeos": False}.items():
        table = local.copy()
        for column in ["latitude", "longitude"]:
            table[column] = emulate(raw[column], single_rounding)
        tables[name], values[name] = table, {c: table[c].astype(float).to_numpy()
                                             for c in ["latitude", "longitude"]}
    local_values = {c: local[c].astype(float).to_numpy() for c in ["latitude", "longitude"]}
    return {
        "environment": {"os": platform.system(), "machine": platform.machine(),
                        "pandas": pd.__version__, "numpy": np.__version__},
        "local_matches_manifest": D.logical_hash(local, ["station_id"]) == expected,
        "emulations": {
            name: {"matches_local_values": all(
                       np.array_equal(values[name][c], local_values[c], equal_nan=True)
                       for c in local_values),
                   "matches_manifest_hash": D.logical_hash(table, ["station_id"]) == expected}
            for name, table in tables.items()},
        "differences_between_emulations": {
            c: {"rows": int((values["un_redondeo"][c] != values["dos_redondeos"][c]).sum()),
                "max_degrees": float(np.nanmax(np.abs(values["un_redondeo"][c]
                                                      - values["dos_redondeos"][c])))}
            for c in local_values},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=C.ROOT)
    args = parser.parse_args()
    result = explain(args.project_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["emulations"]["dos_redondeos"]["matches_manifest_hash"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
