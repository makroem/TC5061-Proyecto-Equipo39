"""Motor de calidad de la etapa 3 con tablas sintéticas; no lee los datos reales de MiBici."""

import json
import os
from pathlib import Path
import subprocess

import numpy as np
import pandas as pd
import pytest

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D
from mibici_equipo39 import features as F
from mibici_equipo39.validation import data_checks as Q

REPO = Path(__file__).resolve().parents[1]
POLICY = REPO / "references" / "etapa3" / "quality_policy.json"
DEEPCHECKS_PYTHON = REPO / ".venv-deepchecks" / ("Scripts/python.exe" if os.name == "nt"
                                                 else "bin/python")
DAYS = {"train": ["2025-10-04", "2025-11-03"], "validation": ["2026-06-06", "2026-07-06"],
        "test": ["2026-08-01", "2026-09-07"]}
STATIONS = [str(i) for i in range(1, 13)]


def write_tables(root, seed=39):
    """Malla estación-hora completa con las mismas tablas y manifiestos que deja la ingesta."""
    rng = np.random.default_rng(seed)
    hours = [pd.Timestamp(d) + pd.Timedelta(hours=h) for days in DAYS.values() for d in days
             for h in range(24)]
    grid = pd.DataFrame([(s, h) for s in STATIONS for h in hours], columns=["station_id", "hour"])
    grid["station_id"] = grid["station_id"].astype("string")
    grid = F.add_calendar_features(grid)
    split = {d: s for s, days in DAYS.items() for d in days}
    metadata = grid[["station_id", "hour"]].rename(columns={"hour": "prediction_time"})
    metadata["split"] = grid["hour"].dt.strftime("%Y-%m-%d").map(split)
    metadata["data_version"] = "sintetica"
    p2 = pd.DataFrame({"capacity": 10.0, "flow_min": rng.integers(-6, 1, len(grid)),
                       "flow_max": rng.integers(0, 7, len(grid))}).astype(
        {"flow_min": "int32", "flow_max": "int32"})
    p2["y_bikes"], p2["y_docks"] = F.proxy_labels(p2["flow_min"], p2["flow_max"], p2["capacity"])
    stations = pd.DataFrame({"station_id": pd.array(STATIONS, dtype="string"),
                             "capacity": pd.array([10] * len(STATIONS), dtype="Int64")})
    processed = root / "data" / "processed"
    processed.mkdir(parents=True)
    metadata.to_parquet(processed / "metadata.parquet", index=False)
    grid[F.FEATURE_COLUMNS].to_parquet(processed / "X_p1.parquet", index=False)
    pd.DataFrame({"target_departures": rng.poisson(5, len(grid))}).to_parquet(
        processed / "y_p1.parquet", index=False)
    p2.to_parquet(processed / "y_p2.parquet", index=False)
    stations.to_parquet(processed / "stations.parquet", index=False)
    (root / "references").mkdir()
    (root / "references" / "data_manifest.json").write_text(json.dumps({
        "data_version": "sintetica", "outputs": {"processed/stations.parquet": {
            "rows": len(STATIONS), "logical_sha256": D.logical_hash(stations, ["station_id"])}}}))
    (root / "references" / "split_manifest.json").write_text(json.dumps({
        "data_version": "sintetica", "split_id": "split-sintetico", "days": DAYS}))
    return processed


def policy_for(root, frozen=False, deepchecks=False, **changes):
    """La política confirmada, con mínimos alcanzables para doce estaciones."""
    policy = json.loads(POLICY.read_text("utf-8"))
    policy["frozen"] = frozen
    for spec in policy["questions"].values():
        if not deepchecks:
            spec["checks"] = [c for c in spec["checks"] if "deepchecks" not in c]
        for check in spec["checks"]:
            if check["check" if "check" in check else "deepchecks"] in changes:
                check["params"] = changes[check.get("check", check.get("deepchecks"))]
            if check.get("check") == "min_positives":
                check["params"] = {"min": 1}
    path = root / "policy.json"
    path.write_text(json.dumps(policy))
    return path



@pytest.fixture
def quality(tmp_path, monkeypatch):
    for key, value in {"ROOT": tmp_path, "DATA": tmp_path / "data",
                       "PROCESSED": tmp_path / "data" / "processed",
                       "REFERENCES": tmp_path / "references"}.items():
        monkeypatch.setattr(C, key, value)
    monkeypatch.setattr(Q, "git_state", lambda: ("a" * 40, False))
    monkeypatch.setattr(Q, "load_deepchecks", lambda: (None, "DeepChecks no disponible"))
    return write_tables(tmp_path)


def run_checks(root, stage="development", **policy):
    output = root / "salida"
    code = Q.main(["--stage", stage, "--policy", str(policy_for(root, **policy)),
                   "--output", str(output)])
    path = output / "summary.json"
    return code, json.loads(path.read_text("utf-8")) if path.exists() else None


def statuses(summary, check_id):
    return {(r["question"], r["split"]): r["status"] for r in summary["results"]
            if r["id"] == check_id}


def test_clean_data_passes_every_integrity_check_and_records_lineage(quality, tmp_path):
    code, summary = run_checks(tmp_path)

    assert code == 0
    assert summary["totals"] == {"PASS": len(summary["results"]), "WARN": 0, "FAIL": 0,
                                 "NOT_EVALUATED": 0}
    assert summary["data_version"] == "sintetica" and summary["split_id"] == "split-sintetico"
    assert summary["commit"] == "a" * 40 and len(summary["policy"]["sha256"]) == 64
    assert summary["created_utc"] and summary["splits"] == ["train", "validation"]
    assert summary["counts"]["p1"]["train"] == {"filas": 576, "estaciones": 12}
    assert summary["counts"]["p3"]["validation"]["filas"] == 12
    assert {r["split"] for r in summary["results"]} == {"todos", "train", "validation",
                                                       "train_vs_validation"}


@pytest.mark.parametrize("damage, check_id", [
    ("duplicate", "llave_unica"),
    ("null", "sin_nulos"),
    ("leak", "variables_del_modelo"),
    ("label", "etiqueta_reproducible"),
    ("negative", "dominios"),
    ("missing_hour", "malla_completa"),
])
def test_critical_damage_fails_with_exit_code_one(quality, tmp_path, damage, check_id):
    processed = quality
    tables = {name: pd.read_parquet(processed / f"{name}.parquet")
              for name in ["metadata", "X_p1", "y_p1", "y_p2"]}
    if damage == "duplicate":
        tables = {k: pd.concat([v, v.iloc[[0]]], ignore_index=True) for k, v in tables.items()}
    elif damage == "null":
        tables["X_p1"]["hour_sin"] = tables["X_p1"]["hour_sin"].astype(float)
        tables["X_p1"].loc[3, "hour_sin"] = np.nan
    elif damage == "leak":
        tables["X_p1"]["flow_min"] = tables["y_p2"]["flow_min"]
    elif damage == "label":
        tables["y_p2"].loc[0, "y_bikes"] = 1 - tables["y_p2"].loc[0, "y_bikes"]
    elif damage == "negative":
        tables["y_p1"].loc[0, "target_departures"] = -1
    elif damage == "missing_hour":
        tables = {k: v.drop(index=5).reset_index(drop=True) for k, v in tables.items()}
    for name, frame in tables.items():
        frame.to_parquet(processed / f"{name}.parquet", index=False)

    code, summary = run_checks(tmp_path)

    assert code == 1
    assert "FAIL" in statuses(summary, check_id).values()


def test_rows_outside_their_manifest_split_fail_lineage(quality, tmp_path):
    metadata = pd.read_parquet(quality / "metadata.parquet")
    metadata.loc[metadata["split"].eq("validation"), "split"] = "train"
    metadata.to_parquet(quality / "metadata.parquet", index=False)

    code, summary = run_checks(tmp_path)

    assert code == 1
    assert statuses(summary, "particion_del_manifiesto") == {("datos", "todos"): "FAIL"}


def test_other_data_version_or_changed_stations_fail_lineage(quality, tmp_path):
    metadata = pd.read_parquet(quality / "metadata.parquet")
    metadata["data_version"] = "otra"
    metadata.to_parquet(quality / "metadata.parquet", index=False)
    stations = pd.read_parquet(quality / "stations.parquet")
    stations.loc[0, "capacity"] = 12
    stations.to_parquet(quality / "stations.parquet", index=False)

    code, summary = run_checks(tmp_path)

    assert code == 1
    assert statuses(summary, "version_de_datos") == {("datos", "todos"): "FAIL"}
    assert statuses(summary, "salidas_del_manifiesto") == {("datos", "todos"): "FAIL"}


def test_unavailable_deepchecks_is_not_evaluated_and_never_counts_as_passed(quality, tmp_path):
    code, summary = run_checks(tmp_path, deepchecks=True)

    deepchecks = [r for r in summary["results"] if r["tool"] == "deepchecks"]
    assert code == 2
    assert deepchecks and {r["status"] for r in deepchecks} == {"NOT_EVALUATED"}
    assert all(r["detail"]["causa"] == "DeepChecks no disponible" for r in deepchecks)
    assert summary["totals"]["FAIL"] == 0


def test_warning_checks_do_not_change_the_exit_code(quality, tmp_path):
    code, summary = run_checks(tmp_path, prevalence_ratio={"range": [5.0, 6.0]})

    assert code == 0
    assert set(statuses(summary, "prevalencia_por_riesgo").values()) == {"WARN"}


def test_final_stage_requires_a_frozen_policy_and_adds_test(quality, tmp_path):
    assert run_checks(tmp_path, stage="final")[0] == 2

    code, summary = run_checks(tmp_path, stage="final", frozen=True)

    assert code == 0 and summary["policy"]["frozen"] is True
    assert summary["splits"] == ["train", "validation", "test"]
    assert ("p2", "train_vs_test") in statuses(summary, "prevalencia_por_riesgo")
    assert summary["counts"]["p2"]["test"]["filas"] == 576


def test_missing_table_is_an_execution_error(quality, tmp_path):
    (quality / "y_p2.parquet").unlink()

    assert Q.main(["--policy", str(policy_for(tmp_path)), "--output",
                   str(tmp_path / "salida")]) == 2
    assert not (tmp_path / "salida" / "summary.json").exists()


def test_profile_blocks_must_sum_to_one_or_zero():
    columns = [f"{d}_hour_{h:02d}" for d in ["weekday", "weekend"] for h in range(24)]
    good = pd.DataFrame([[1 / 24] * 24 + [0.0] * 24], columns=columns)
    bad = good.copy()
    bad.loc[0, "weekday_hour_00"] = 0.5

    assert Q.integrity_check("profile_sums", {"tolerance": 1e-6}, good, {}, "train", {})[0]
    assert Q.integrity_check("profile_sums", {"tolerance": 1e-6}, bad, {}, "train", {}) == (
        False, {"bloques_invalidos": {"weekday_hour": 1}})


@pytest.mark.integration
@pytest.mark.skipif(not DEEPCHECKS_PYTHON.exists(), reason="Falta .venv-deepchecks")
@pytest.mark.parametrize("constant, expected", [(False, 0), (True, 1)])
def test_deepchecks_environment_runs_the_policy_and_detects_a_constant_feature(
        tmp_path, constant, expected):
    processed = write_tables(tmp_path)
    if constant:
        X = pd.read_parquet(processed / "X_p1.parquet")
        X["is_weekend"] = 0
        X.to_parquet(processed / "X_p1.parquet", index=False)
    env = {**os.environ, "MIBICI_PROJECT_ROOT": str(tmp_path), "PYTHONPATH": str(REPO)}
    result = subprocess.run(
        [str(DEEPCHECKS_PYTHON), "-m", "mibici_equipo39.validation.data_checks",
         "--policy", str(policy_for(tmp_path, deepchecks=True)),
         "--output", str(tmp_path / "salida")],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=600)
    summary = json.loads((tmp_path / "salida" / "summary.json").read_text("utf-8"))

    assert result.returncode == expected, result.stdout + result.stderr
    assert summary["environment"]["deepchecks"] == "0.19.1"
    assert summary["totals"]["NOT_EVALUATED"] == 0
    assert (tmp_path / "salida" / "deepchecks.html").exists()
    constant_status = statuses(summary, "variable_constante")
    assert (constant_status[("p1", "train")] == "FAIL") is constant
