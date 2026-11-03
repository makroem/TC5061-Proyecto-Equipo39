"""Verifica el paquete completo antes de deserializar un modelo de confianza."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

import mlflow.pyfunc
from mlflow.models import Model


def inventory(folder):
    """Hashes por ruta relativa; rechaza enlaces y no omite archivos adicionales."""
    folder = Path(folder)
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("El paquete no es un directorio local válido.")
    files = {}
    for path in sorted(folder.rglob("*")):
        if path.is_symlink():
            raise ValueError("El paquete no puede contener enlaces simbólicos.")
        if path.is_file():
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            files[path.relative_to(folder).as_posix()] = digest.hexdigest()
    if "MLmodel" not in files:
        raise ValueError("Falta MLmodel en el paquete.")
    return files


def bundle_digest(files):
    """Identificador del inventario ordenado, independiente de la ruta local."""
    encoded = json.dumps(files, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_manifest(path):
    """Valida formato y huellas; la autenticidad del manifiesto depende de su revisión en Git."""
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"schema_version", "model_name", "model_version", "source_run_id",
                "training_commit", "data_version", "signature", "files", "bundle_sha256"}
    if not isinstance(manifest, dict) or not required.issubset(manifest):
        raise ValueError("Manifiesto incompleto.")
    if manifest["schema_version"] != 1:
        raise ValueError("Versión de manifiesto no compatible.")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", str(manifest["model_name"])):
        raise ValueError("Nombre de modelo inválido.")
    if not re.fullmatch(r"[1-9][0-9]*", str(manifest["model_version"])):
        raise ValueError("Versión numérica inválida.")
    for key, length in (("source_run_id", 32), ("training_commit", 40), ("data_version", 64)):
        if not re.fullmatch(r"[0-9a-f]{%d}" % length, str(manifest[key])):
            raise ValueError(f"Linaje inválido: {key}.")
    files = manifest["files"]
    if not isinstance(files, dict) or "MLmodel" not in files:
        raise ValueError("Inventario incompleto.")
    for name, digest in files.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or ".." in relative.parts or "\\" in name
                or ":" in name or relative.as_posix() != name):
            raise ValueError("Ruta inválida en el inventario.")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Hash inválido en el inventario.")
    if bundle_digest(files) != manifest["bundle_sha256"]:
        raise ValueError("El inventario no coincide con su hash.")
    if not isinstance(manifest["signature"], dict) or not manifest["signature"].get("inputs"):
        raise ValueError("Falta firma de entrada.")
    return manifest


def package_metadata(folder):
    """Lee metadatos YAML sin cargar el objeto serializado."""
    metadata = Model.load(str(Path(folder) / "MLmodel"))
    if not metadata.signature or "python_function" not in metadata.flavors:
        raise ValueError("El modelo requiere firma y flavor python_function.")
    # El paquete completo debe ser autocontenido para su copia a una imagen.
    flavor = metadata.flavors["python_function"]
    for key in ("data", "code", "model_path"):
        if value := flavor.get(key):
            target = PurePosixPath(value)
            if target.is_absolute() or ".." in target.parts or ":" in value or "\\" in value:
                raise ValueError("El modelo referencia archivos fuera del paquete.")
            if not (Path(folder) / value).exists():
                raise ValueError(f"Falta archivo declarado por MLmodel: {key}.")
    return metadata


def verify_bundle(folder, manifest):
    """Rechaza archivos faltantes, extra, cambiados y una firma o run diferentes."""
    if inventory(folder) != manifest["files"]:
        raise ValueError("El paquete no coincide con el inventario aprobado.")
    metadata = package_metadata(folder)
    if metadata.signature.to_dict() != manifest["signature"]:
        raise ValueError("La firma no coincide con el manifiesto.")
    if metadata.run_id != manifest["source_run_id"]:
        raise ValueError("El run del paquete no coincide con el manifiesto.")
    return metadata


@dataclass(frozen=True)
class LoadedModel:
    model: object
    manifest: dict

    def predict(self, frame):
        return self.model.predict(frame)


def load_model(model_dir, manifest_path):
    """Solo acepta paquete local y manifiesto configurados por el operador."""
    manifest = read_manifest(manifest_path)
    verify_bundle(model_dir, manifest)
    model = mlflow.pyfunc.load_model(str(Path(model_dir).resolve()))
    return LoadedModel(model=model, manifest=manifest)
