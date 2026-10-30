"""Calidad de los datos preparados con reglas de integridad y DeepChecks.

Lee las tablas de data/processed, confirma que correspondan a los manifiestos oficiales y aplica
references/etapa3/quality_policy.json. Se ejecuta en .venv-deepchecks; si DeepChecks no se puede
importar, sus comprobaciones quedan NOT_EVALUATED y nunca cuentan como aprobadas.

Salida 0: obligatorias completas sin fallos; 1: fallo crítico de datos; 2: error de ejecución
o comprobación obligatoria sin evaluar.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
from types import SimpleNamespace

import numpy as np
import pandas as pd

from mibici_equipo39 import config as C
from mibici_equipo39 import dataset as D
from mibici_equipo39 import features as F

STAGES = {"development": ["train", "validation"], "final": ["train", "validation", "test"]}
QUESTIONS = ["p1", "p2", "p3"]


def policy_path():
    return C.REFERENCES / "etapa3" / "quality_policy.json"


def status_of(passed, severity):
    return "PASS" if passed else ("FAIL" if severity == "critical" else "WARN")


def git_state():
    git = shutil.which("git")
    if git is None:
        return None, None
    head = subprocess.run([git, "rev-parse", "HEAD"], cwd=C.ROOT, capture_output=True, text=True)
    if head.returncode:
        return None, None
    dirty = subprocess.run([git, "status", "--porcelain"], cwd=C.ROOT,
                           capture_output=True, text=True)
    return head.stdout.strip(), bool(dirty.stdout.strip())


def load_deepchecks():
    os.environ.setdefault("DISABLE_LATEST_VERSION_CHECK", "True")
    try:
        import deepchecks
        from deepchecks.core.check_result import CheckResult
        from deepchecks.core.suite import SuiteResult
        from deepchecks.tabular import Dataset, checks
    # Con NumPy 2 la importación falla con AttributeError (np.Inf), no con ImportError.
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"
    return SimpleNamespace(version=deepchecks.__version__, Dataset=Dataset, checks=checks,
                           CheckResult=CheckResult, SuiteResult=SuiteResult), None


def load_inputs():
    metadata, X, y_p1 = F.load_tables()
    return {
        "metadata": metadata, "X": X, "y_p1": y_p1, "y_p2": F.load_p2_targets(),
        "data_manifest": json.loads((C.REFERENCES / "data_manifest.json").read_text("utf-8")),
        "split_manifest": json.loads((C.REFERENCES / "split_manifest.json").read_text("utf-8")),
    }


def lineage_check(name, inputs):
    meta, data_m, split_m = inputs["metadata"], inputs["data_manifest"], inputs["split_manifest"]
    if name == "data_version":
        found = sorted(meta["data_version"].astype(str).unique())
        expected = {data_m["data_version"], split_m["data_version"]}
        return found == sorted(expected) and len(expected) == 1, {
            "tablas": found, "data_manifest": data_m["data_version"],
            "split_manifest": split_m["data_version"]}
    if name == "aligned_tables":
        rows = {k: len(inputs[k]) for k in ["metadata", "X", "y_p1", "y_p2"]}
        return len(set(rows.values())) == 1, {"filas": rows}
    if name == "split_days":
        expected = pd.Series({d: s for s, days in split_m["days"].items() for d in days})
        day = meta["prediction_time"].dt.strftime("%Y-%m-%d")
        wrong = int(day.map(expected).ne(meta["split"]).sum())
        return wrong == 0, {"filas_fuera_de_su_conjunto": wrong, "split_id": split_m["split_id"]}
    if name == "manifest_outputs":
        bad = []
        for relative, info in data_m["outputs"].items():
            path = C.DATA / relative
            if not path.exists():
                bad.append({"archivo": relative, "causa": "no existe"})
                continue
            frame = pd.read_parquet(path)
            key = ["station_id"] if relative.endswith("stations.parquet") else ["trip_id"]
            if len(frame) != info["rows"] or D.logical_hash(frame, key) != info["logical_sha256"]:
                bad.append({"archivo": relative, "filas": len(frame), "filas_esperadas": info["rows"],
                            "causa": "filas o hash lógico distintos"})
        return not bad, {"archivos": len(data_m["outputs"]), "distintos": bad}
    raise ValueError(f"Comprobación de linaje desconocida: {name}")


def question_frames(question, inputs, splits):
    """Tablas por conjunto tal como las consumen los adaptadores de la etapa 2."""
    meta, X, y = inputs["metadata"], inputs["X"], inputs["y_p1"]
    base = meta[["station_id", "prediction_time", "split"]]
    # Una columna filtrada a X se reporta en variables_del_modelo; aquí no debe duplicar nombres.
    X = X[[c for c in X.columns if c not in base and c not in inputs["y_p2"]]]
    if question == "p1":
        frame = pd.concat([base, X, y.rename("target_departures")], axis=1)
        frame = frame.loc[meta["station_id"].isin(F.eligible_stations(meta, y))]
    elif question == "p2":
        frame = pd.concat([base, X, inputs["y_p2"]], axis=1)
        frame = frame.loc[frame["capacity"].notna()]
    else:
        # Misma elegibilidad que P3Adapter.load_data: solo viajes de train.
        train = meta["split"].eq("train")
        totals = y[train].groupby(meta.loc[train, "station_id"], observed=True).sum()
        stations = sorted(totals[totals.ge(C.P3_MIN_TRAIN_TRIPS)].index.astype(str))
        frame = base.assign(departures=y.to_numpy())
        return {s: F.station_usage_profiles(frame.loc[frame["split"].eq(s)], stations)
                .rename_axis("station_id").reset_index() for s in splits}
    return {s: frame.loc[frame["split"].eq(s)].reset_index(drop=True) for s in splits}


def data_columns(spec, frame):
    if spec["features"] == "profile":
        return [c for c in frame.columns if c != "station_id"]
    labels = spec.get("labels") or [spec["label"]]
    return list(dict.fromkeys(spec["features"] + labels + spec["key"]))


def integrity_check(name, params, frame, spec, split, inputs, train=None):
    if name == "prevalence_ratio":
        low, high = params["range"]
        ratios = {label: float(frame[label].mean() / train[label].mean()) for label in spec["labels"]}
        return all(low <= r <= high for r in ratios.values()), {
            "razon_contra_train": {k: round(v, 3) for k, v in ratios.items()}}
    if name == "columns":
        if "exact" in params:
            found = list(inputs["X"].columns)
            return found == params["exact"], {"columnas_x": found}
        profile = [c for c in frame.columns if c.startswith(tuple(params["prefixes"]))]
        return len(profile) == params["count"] == len(frame.columns) - 1, {"columnas": len(profile)}
    if name == "nulls":
        nulls = frame[data_columns(spec, frame)].isna().sum()
        return int(nulls.sum()) == 0, {"nulos": {k: int(v) for k, v in nulls.items() if v}}
    if name == "unique_key":
        repeated = int(frame.duplicated(spec["key"]).sum())
        return repeated == 0, {"repetidos": repeated}
    if name == "domain":
        out = {}
        for column, (low, high) in params["ranges"].items():
            values = pd.to_numeric(frame[column], errors="coerce")
            bad = values.isna() | (values.lt(low) if low is not None else False)
            bad |= values.gt(high) if high is not None else False
            if column in params.get("integer", []):
                bad |= values.mod(1).ne(0)
            if bad.any():
                out[column] = int(bad.sum())
        return not out, {"fuera_de_dominio": out}
    if name == "complete_grid":
        hours = 24 * len(inputs["split_manifest"]["days"][split])
        stations = frame["station_id"].nunique()
        return len(frame) == stations * hours, {"filas": len(frame), "estaciones": stations,
                                                "horas": hours}
    if name == "min_entities":
        stations = frame["station_id"].nunique()
        return stations >= params["min"], {"estaciones": stations, "minimo": params["min"]}
    if name == "min_positives":
        positives = {label: int(frame[label].sum()) for label in spec["labels"]}
        return min(positives.values()) >= params["min"], {"positivos": positives,
                                                          "minimo": params["min"]}
    if name == "p2_labels":
        y_bikes, y_docks = F.proxy_labels(frame["flow_min"], frame["flow_max"], frame["capacity"])
        wrong = {"y_bikes": int(y_bikes.ne(frame["y_bikes"]).sum()),
                 "y_docks": int(y_docks.ne(frame["y_docks"]).sum())}
        return not any(wrong.values()), {"distintas": wrong}
    if name == "profile_sums":
        out = {}
        for prefix in ["weekday_hour_", "weekend_hour_"]:
            sums = frame[[c for c in frame.columns if c.startswith(prefix)]].sum(axis=1)
            ok = sums.sub(1).abs().le(params["tolerance"]) | sums.eq(0)
            if not ok.all():
                out[prefix.rstrip("_")] = int((~ok).sum())
        return not out, {"bloques_invalidos": out}
    raise ValueError(f"Comprobación de integridad desconocida: {name}")


def deepchecks_dataset(dc, spec, frame, label, seed, rows):
    sample = frame.sample(n=min(rows, len(frame)), random_state=seed) if rows else frame
    if spec["features"] == "profile":
        columns, cat = [c for c in frame.columns if c != "station_id"], []
    else:
        columns, cat = spec["features"], spec["cat_features"]
    data = sample[columns + ([label] if label else [])].reset_index(drop=True)
    label_type = spec.get("label_type") if label else None
    return dc.Dataset(data, label=label, cat_features=cat, features=columns, label_type=label_type)


def deepchecks_check(dc, entry):
    check = getattr(dc.checks, entry["deepchecks"])(**entry.get("init", {}))
    return getattr(check, entry["condition"])(**entry.get("params", {}))


def deepchecks_status(dc, result, severity):
    if not isinstance(result, dc.CheckResult):
        return "NOT_EVALUATED", {"causa": str(getattr(result, "exception", result))}
    if not result.have_conditions() or not result.conditions_results:
        return "NOT_EVALUATED", {"causa": "la comprobación no evaluó su condición"}
    passed = all(c.is_pass() for c in result.conditions_results)
    return status_of(passed, severity), {"condiciones": [c.details for c in result.conditions_results]}


def run_question(question, spec, inputs, splits, dc, dc_error, policy, html):
    results, counts = [], {}
    frames = question_frames(question, inputs, splits)
    labels = spec.get("labels") or ([spec["label"]] if spec.get("label") else [None])
    for split, frame in frames.items():
        counts[split] = {"filas": len(frame), "estaciones": int(frame["station_id"].nunique())}
        if question == "p2":
            counts[split]["positivos"] = {k: int(frame[k].sum()) for k in spec["labels"]}
    for entry in spec["checks"]:
        record = {"question": question, "id": entry["id"], "severity": entry["severity"]}
        pairs = ([(s, None) for s in splits] if entry.get("mode", "single") == "single"
                 else [("train", s) for s in splits if s != "train"])
        if "check" in entry:
            for first, second in pairs:
                passed, detail = integrity_check(entry["check"], entry.get("params", {}),
                                                 frames[second or first], spec, second or first,
                                                 inputs, frames[first] if second else None)
                results.append({**record, "split": f"{first}_vs_{second}" if second else first,
                                "tool": "integridad",
                                "status": status_of(passed, entry["severity"]), "detail": detail})
            continue
        uses_label = entry["deepchecks"] in {"FeatureLabelCorrelation", "LabelDrift"}
        for first, second in pairs:
            for label in (labels if uses_label else [labels[0]]):
                target = f"{first}_vs_{second}" if second else first
                row = {**record, "split": target, "tool": "deepchecks",
                       **({"label": label} if uses_label and label else {})}
                if dc is None:
                    results.append({**row, "status": "NOT_EVALUATED",
                                    "detail": {"causa": dc_error}})
                    continue
                datasets = [deepchecks_dataset(dc, spec, frames[s], label, policy["seed"],
                                               policy["deepchecks_sample_rows"])
                            for s in [first, second] if s]
                try:
                    result = deepchecks_check(dc, entry).run(*datasets)
                except Exception as exc:
                    result = exc
                status, detail = deepchecks_status(dc, result, entry["severity"])
                results.append({**row, "status": status, "detail": detail})
                if isinstance(result, dc.CheckResult):
                    html.append(result)
    return results, counts


def exit_code(results):
    if any(r["status"] == "FAIL" for r in results):
        return 1
    if any(r["status"] == "NOT_EVALUATED" and r["severity"] == "critical" for r in results):
        return 2
    return 0


def run(questions, stage, policy_file, output):
    raw = policy_file.read_bytes()
    policy = json.loads(raw)
    if stage == "final" and not policy.get("frozen"):
        raise ValueError("La etapa final requiere una política congelada (frozen: true).")
    splits = STAGES[stage]
    dc, dc_error = load_deepchecks()
    inputs = load_inputs()
    results = []
    for entry in policy["lineage"]:
        passed, detail = lineage_check(entry["check"], inputs)
        results.append({"question": "datos", "id": entry["id"], "severity": entry["severity"],
                        "split": "todos", "tool": "integridad",
                        "status": status_of(passed, entry["severity"]), "detail": detail})
    counts, html = {}, []
    for question in questions:
        found, counts[question] = run_question(question, policy["questions"][question], inputs,
                                               splits, dc, dc_error, policy, html)
        results.extend(found)
    commit, dirty = git_state()
    code = exit_code(results)
    summary = {
        "stage": stage, "questions": questions, "splits": splits,
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit, "git_dirty": dirty,
        "data_version": inputs["data_manifest"]["data_version"],
        "split_id": inputs["split_manifest"]["split_id"],
        "policy": {"path": policy_file.name, "sha256": hashlib.sha256(raw).hexdigest(),
                   "version": policy["version"], "frozen": bool(policy.get("frozen"))},
        "environment": {"python": platform.python_version(), "pandas": pd.__version__,
                        "numpy": np.__version__,
                        "deepchecks": dc.version if dc else f"no disponible ({dc_error})"},
        "deepchecks_sample_rows": policy["deepchecks_sample_rows"],
        "counts": counts,
        "totals": {s: sum(r["status"] == s for r in results)
                   for s in ["PASS", "WARN", "FAIL", "NOT_EVALUATED"]},
        "exit_code": code,
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    if html:
        dc.SuiteResult(f"Calidad {stage}", html).save_as_html(
            str(output / "deepchecks.html"), as_widget=False, connected=False)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--question", choices=["all", *QUESTIONS], default="all")
    parser.add_argument("--stage", choices=list(STAGES), default="development")
    parser.add_argument("--policy", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args(argv)
    questions = QUESTIONS if args.question == "all" else [args.question]
    output = args.output or C.ROOT / "private_quality" / "data_checks" / args.stage
    try:
        summary = run(questions, args.stage, args.policy or policy_path(), output)
    except (FileNotFoundError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error de ejecución: {type(exc).__name__}: {exc}")
        return 2
    for r in summary["results"]:
        if r["status"] != "PASS":
            print(f"{r['status']:13} {r['question']:5} {r['split']:22} {r['id']}")
    print(json.dumps({k: summary[k] for k in ["stage", "totals", "exit_code"]}, ensure_ascii=False))
    return summary["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
