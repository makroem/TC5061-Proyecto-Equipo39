"""Crea un respaldo y una copia aislada de un almacén SQLite local de MLflow.

La base de origen se abre en modo lectura. Este paso no actualiza su esquema.
Los destinos deben ser nuevos y ajenos al directorio de origen.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
from urllib.parse import urlparse
from urllib.request import url2pathname


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_paths(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if not source.is_dir() or not (source / "mlflow.db").is_file():
        raise ValueError("El origen debe contener mlflow.db.")
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("El destino y el origen no pueden solaparse.")
    if destination.exists():
        raise FileExistsError("El destino ya existe; usar una carpeta nueva.")
    return source, destination


def artifact_inventory(root):
    files = {}
    for name in ("mlruns", "mlartifacts"):
        folder = root / name
        if folder.exists():
            for path in sorted(folder.rglob("*")):
                if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
                    raise ValueError("El almacén contiene un enlace externo o simbólico.")
                if path.is_file():
                    files[path.relative_to(root).as_posix()] = digest(path)
    return files


def relocate_uri(value, source, target):
    if not value:
        return value
    parsed = urlparse(value)
    if parsed.scheme == "file" and not parsed.netloc:
        path = Path(url2pathname(parsed.path)).resolve()
        if not path.is_relative_to(source):
            raise ValueError("Hay un artefacto fuera del origen; no se copia automáticamente.")
        return (target / path.relative_to(source)).as_uri()
    if value.startswith("mlflow-artifacts:/"):
        relative = value[len("mlflow-artifacts:/"):].lstrip("/")
        path = (target / "mlartifacts" / relative).resolve()
        if not path.is_relative_to(target):
            raise ValueError("La ruta de artefactos sale del destino.")
        return path.as_uri()
    if value.startswith(("runs:/", "models:/")):
        return value
    raise ValueError("URI de artefacto no local o no compatible con este procedimiento.")


def relocate_database(database, source, target):
    """Cambia únicamente ubicaciones en una copia; conserva IDs, métricas y alias."""
    with sqlite3.connect(database) as db:
        statements = [
            ("SELECT rowid, artifact_location FROM experiments",
             "UPDATE experiments SET artifact_location=? WHERE rowid=?"),
            ("SELECT rowid, artifact_uri FROM runs", "UPDATE runs SET artifact_uri=? WHERE rowid=?"),
            ("SELECT rowid, source FROM model_versions", "UPDATE model_versions SET source=? WHERE rowid=?"),
        ]
        if "storage_location" in {r[1] for r in db.execute("PRAGMA table_info(model_versions)")}:
            statements.append(("SELECT rowid, storage_location FROM model_versions",
                               "UPDATE model_versions SET storage_location=? WHERE rowid=?"))
        for select, update in statements:
            for rowid, value in db.execute(select).fetchall():
                db.execute(update, (relocate_uri(value, source, target), rowid))
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Falló la integridad de la copia SQLite.")


def logical_inventory(database, reference=None):
    """Huella del contenido previo, excluyendo ubicaciones reescritas y el esquema."""
    excluded = {"experiments": {"artifact_location"}, "runs": {"artifact_uri"},
                "model_versions": {"source", "storage_location"}}
    queries = {
        "experiments": "SELECT * FROM experiments", "runs": "SELECT * FROM runs",
        "metrics": "SELECT * FROM metrics", "latest_metrics": "SELECT * FROM latest_metrics",
        "params": "SELECT * FROM params", "tags": "SELECT * FROM tags",
        "registered_models": "SELECT * FROM registered_models",
        "registered_model_tags": "SELECT * FROM registered_model_tags",
        "model_versions": "SELECT * FROM model_versions",
        "model_version_tags": "SELECT * FROM model_version_tags",
        "registered_model_aliases": "SELECT * FROM registered_model_aliases",
    }
    result = {}
    with sqlite3.connect(database.as_uri() + "?mode=ro", uri=True) as db:
        available = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table, query in queries.items():
            if table not in available:
                continue
            cursor = db.execute(query)
            all_columns = [c[0] for c in cursor.description]
            columns = (reference[table]["columns"] if reference else
                       [c for c in all_columns if c not in excluded.get(table, set())])
            positions = [all_columns.index(c) for c in columns]
            rows = [tuple(row[i] for i in positions) for row in cursor.fetchall()]
            payload = json.dumps(sorted(rows, key=repr), ensure_ascii=False, separators=(",", ":"))
            result[table] = {"columns": columns, "rows": len(rows),
                             "sha256": hashlib.sha256(payload.encode()).hexdigest()}
    return result


def prepare(source, destination):
    source, destination = validate_paths(source, destination)
    before = artifact_inventory(source)
    initial_db = digest(source / "mlflow.db")
    destination.mkdir(parents=True, exist_ok=False)
    backup = destination / "backup"
    candidate = destination / "candidate"
    backup.mkdir()
    with sqlite3.connect((source / "mlflow.db").as_uri() + "?mode=ro", uri=True) as src:
        with sqlite3.connect(backup / "mlflow.db") as dst:
            src.backup(dst)
    for name in ("mlruns", "mlartifacts"):
        if (source / name).exists():
            shutil.copytree(source / name, backup / name)
    if before != artifact_inventory(source) or before != artifact_inventory(backup):
        raise RuntimeError("Los artefactos cambiaron durante el respaldo; repetir sin escritores.")
    if initial_db != digest(source / "mlflow.db"):
        raise RuntimeError("La base de origen cambió durante el respaldo; repetir sin escritores.")
    shutil.copytree(backup, candidate)
    relocate_database(candidate / "mlflow.db", source, candidate)
    logical = logical_inventory(backup / "mlflow.db")
    if logical != logical_inventory(candidate / "mlflow.db"):
        raise RuntimeError("La copia no conserva el contenido lógico.")
    (destination / "private_origin.json").write_text(json.dumps({
        "source": str(source), "source_db_sha256": initial_db,
        "artifacts": before, "tables": logical,
    }, indent=2), encoding="utf-8")
    summary = {"status": "PREPARED", "artifact_files": len(before),
               "source_unchanged": True, "logical_content_preserved": True,
               "backup_db_sha256": digest(backup / "mlflow.db"),
               "runs": logical["runs"]["rows"], "model_versions": logical["model_versions"]["rows"]}
    (destination / "prepare_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def restore_copy(root):
    """Ensaya la recuperación del respaldo en otra carpeta, sin tocar el servidor."""
    root = Path(root).resolve()
    backup, restored = root / "backup", root / "restored"
    record = json.loads((root / "private_origin.json").read_text(encoding="utf-8"))
    summary = json.loads((root / "prepare_summary.json").read_text(encoding="utf-8"))
    if restored.exists():
        raise FileExistsError("La copia restaurada ya existe.")
    if digest(backup / "mlflow.db") != summary["backup_db_sha256"]:
        raise ValueError("La base de respaldo fue modificada.")
    if artifact_inventory(backup) != record["artifacts"]:
        raise ValueError("Los artefactos del respaldo fueron modificados.")
    shutil.copytree(backup, restored)
    relocate_database(restored / "mlflow.db", Path(record["source"]), restored)
    if logical_inventory(restored / "mlflow.db") != record["tables"]:
        raise RuntimeError("La recuperación no conserva el contenido lógico.")
    return {"status": "RESTORED_COPY", "logical_content_preserved": True,
            "artifact_files": len(record["artifacts"])}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--restore", type=Path, help="Carpeta de un ensayo preparado; crea restored/.")
    args = parser.parse_args()
    if args.restore:
        if args.source or args.destination:
            parser.error("--restore no se combina con --source/--destination")
        result = restore_copy(args.restore)
    else:
        if not args.source or not args.destination:
            parser.error("Se requieren --source y --destination")
        result = prepare(args.source, args.destination)
    print(json.dumps(result, indent=2))
