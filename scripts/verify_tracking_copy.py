"""Comprueba contenido y predicciones en candidate/ o restored/ de un ensayo."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import sqlite3

import mlflow

from prepare_tracking_migration import artifact_inventory, digest, logical_inventory
from mibici_equipo39 import config as C
from mibici_equipo39 import registry


def verify(root, name):
    root = root.resolve()
    store = root / name
    record = json.loads((root / "private_origin.json").read_text(encoding="utf-8"))
    database = store / "mlflow.db"
    if not database.is_file() or store.resolve().parent != root:
        raise ValueError("No existe una copia aislada válida.")
    inventory = logical_inventory(database, record["tables"])
    if inventory != record["tables"]:
        raise ValueError("Cambió el contenido de corridas, métricas, parámetros, etiquetas o registro.")
    if artifact_inventory(store) != record["artifacts"]:
        raise ValueError("Los artefactos no coinciden con el respaldo.")
    uri = "sqlite:///" + database.as_posix()
    C.TRACKING_URI = C.REGISTRY_URI = uri
    loads = registry.verify(list(C.REGISTERED_MODELS))
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        schema = db.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        integrity = db.execute("PRAGMA integrity_check").fetchone()[0]
    source_unchanged = digest(Path(record["source"]) / "mlflow.db") == record["source_db_sha256"]
    if not source_unchanged or integrity != "ok":
        raise ValueError("Falló la integridad o cambió el origen durante el ensayo.")
    result = {
        "status": "PASS", "store": name,
        "mlflow": mlflow.__version__, "pyarrow": importlib.metadata.version("pyarrow"),
        "schema_revision": schema, "integrity": integrity,
        "runs_preserved": inventory["runs"]["rows"],
        "model_versions_preserved": inventory["model_versions"]["rows"],
        "historical_tables": inventory, "artifact_files_preserved": len(record["artifacts"]),
        "source_unchanged": source_unchanged, "models": loads,
    }
    (root / f"{name}_verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--store", choices=("candidate", "restored"), required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.root, args.store), indent=2))
