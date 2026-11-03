"""Descarga una versión del Registry sin entrenar, registrar ni cambiar aliases."""

import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile

import mlflow
from mlflow import MlflowClient

from mibici_equipo39.serving import settings
from mibici_equipo39.serving.model_loader import (
    bundle_digest, inventory, package_metadata, read_manifest, verify_bundle,
)


def export_model(*, output, name=None, alias=None, manifest=None, manifest_out=None):
    """Resuelve alias una vez, o reproduce la versión y hashes de un manifiesto."""
    if bool(name) == bool(manifest):
        raise ValueError("Indique name o manifest, exclusivamente.")
    if manifest and (alias or manifest_out):
        raise ValueError("La reproducción no admite alias ni otro manifiesto de salida.")
    tracking = os.environ.get("MLFLOW_TRACKING_URI")
    registry = os.environ.get("MLFLOW_REGISTRY_URI", tracking)
    if not tracking or not registry:
        raise ValueError("Configure MLFLOW_TRACKING_URI para el almacén oficial.")
    expected = read_manifest(manifest) if manifest else None
    output = Path(output)
    target_manifest = Path(manifest_out or settings.DEFAULT_MANIFEST) if not expected else None
    if output.exists() and not expected:
        raise FileExistsError("El destino existe; use --manifest para comprobarlo sin sobrescribir.")
    if target_manifest and target_manifest.exists():
        raise FileExistsError("El manifiesto existe; utilice --manifest para reproducirlo.")
    if target_manifest and target_manifest.resolve().is_relative_to(output.resolve()):
        raise ValueError("El manifiesto debe guardarse fuera del paquete del modelo.")
    client = MlflowClient(tracking_uri=tracking, registry_uri=registry)
    if expected:
        version = client.get_model_version(expected["model_name"], expected["model_version"])
    else:
        version = client.get_model_version_by_alias(name, alias or settings.MODEL_ALIAS)
    if version.status != "READY":
        raise ValueError("La versión del modelo no está lista.")
    run = client.get_run(version.run_id)
    tags, params = run.data.tags, run.data.params
    lineage = {
        "model_name": version.name,
        "model_version": str(version.version),
        "source_run_id": version.run_id,
        "training_commit": tags.get("git_commit") or tags.get("mlflow.source.git.commit"),
        "data_version": params.get("data_version") or version.tags.get("data_version"),
    }
    if expected and any(expected[key] != value for key, value in lineage.items()):
        raise ValueError("El linaje del Registry cambió respecto al manifiesto.")
    if output.exists():
        verify_bundle(output, expected)
        return expected
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="export-p1-", dir=output.parent) as temp:
        downloaded = Path(mlflow.artifacts.download_artifacts(
            artifact_uri=f"models:/{version.name}/{version.version}",
            dst_path=str(Path(temp) / "download"), tracking_uri=tracking, registry_uri=registry,
        ))
        files = inventory(downloaded)
        metadata = package_metadata(downloaded)
        resolved = expected or {
            "schema_version": 1, **lineage,
            "resolved_alias": alias or settings.MODEL_ALIAS,
            "signature": metadata.signature.to_dict(),
            "files": files, "bundle_sha256": bundle_digest(files),
        }
        temporary_manifest = Path(temp) / "manifest.json"
        temporary_manifest.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")
        resolved = read_manifest(temporary_manifest)
        verify_bundle(downloaded, resolved)
        staged = Path(temp) / "bundle"
        shutil.copytree(downloaded, staged)
        verify_bundle(staged, resolved)
        # Destino nuevo: nunca borra ni sustituye un paquete anterior.
        staged.rename(output)
        if target_manifest:
            target_manifest.parent.mkdir(parents=True, exist_ok=True)
            with target_manifest.open("x", encoding="utf-8") as stream:
                json.dump(resolved, stream, indent=2)
                stream.write("\n")
        return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--name")
    group.add_argument("--manifest", type=Path)
    parser.add_argument("--alias")
    parser.add_argument("--output", type=Path, default=settings.DEFAULT_MODEL_DIR)
    parser.add_argument("--manifest-out", type=Path)
    args = parser.parse_args()
    result = export_model(**vars(args))
    print(json.dumps({key: result[key] for key in (
        "model_name", "model_version", "source_run_id", "bundle_sha256")}, indent=2))


if __name__ == "__main__":
    main()
