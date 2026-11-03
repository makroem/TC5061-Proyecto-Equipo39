"""Adapta dos utilidades de DeepChecks 0.19.1 a setuptools sin pkg_resources.

Ejecutar después de instalar requirements-deepchecks.txt. La adaptación conserva
los avisos de licencia originales y no cambia comprobaciones, métricas ni umbrales.
Se rechazan versiones o archivos distintos de los verificados, antes de escribir.
"""

import hashlib
from importlib import metadata
import json
from pathlib import Path


PATCHES = {
    "utils/display.py": {
        "sha256": "c41da32ba473058d848434942d1416431e110aa89031ddc8639cc787ec30c612",
        "replacements": [
            ("import pkg_resources", "from importlib.metadata import distributions\n"
             "from packaging.utils import canonicalize_name"),
            ("{pkg.key for pkg in list(pkg_resources.working_set)}",
             "{canonicalize_name(pkg.metadata['Name']) for pkg in distributions() "
             "if pkg.metadata['Name']}"),
        ],
    },
    "core/serialization/dataframe/html.py": {
        "sha256": "73e96417a059e3784851f71fe8daf382260350173f16ceadbdf30d23b04a9c3d",
        "replacements": [
            ("from pkg_resources import parse_version", "from packaging.version import parse as parse_version"),
        ],
    },
}
NOTICE = "# Adaptacion local Equipo 39: importlib.metadata y packaging; 2026-11-02.\n"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def adapted_bytes(original, replacements):
    text = original.decode("utf-8")
    for old, new in replacements:
        if text.count(old) != 1:
            raise ValueError("La expresion a sustituir no aparece exactamente una vez")
        text = text.replace(old, new)
    return (NOTICE + text).encode("utf-8")


def prepare(root, version):
    """Valida los dos archivos y aplica la adaptación una sola vez."""
    if version != "0.19.1":
        raise ValueError("Esta adaptacion solo esta verificada para DeepChecks 0.19.1")
    root = Path(root).resolve()
    pending = []
    records = []
    for relative, spec in PATCHES.items():
        path = root / relative
        current = path.read_bytes()
        if current.startswith(NOTICE.encode()):
            original = current[len(NOTICE.encode()):].decode("utf-8")
            for old, new in reversed(spec["replacements"]):
                if original.count(new) != 1:
                    raise ValueError(f"Adaptacion desconocida: {relative}")
                original = original.replace(new, old)
            original = original.encode("utf-8")
        else:
            original = current
        if digest(original) != spec["sha256"]:
            raise ValueError(f"Archivo distinto del paquete verificado: {relative}")
        adapted = adapted_bytes(original, spec["replacements"])
        if current not in (original, adapted):
            raise ValueError(f"Contenido inesperado: {relative}")
        records.append({"file": relative, "original_sha256": digest(original),
                        "adapted_sha256": digest(adapted), "changed": current != adapted})
        if current != adapted:
            pending.append((path, adapted))
    # Toda la validación termina antes de la primera escritura.
    for path, data in pending:
        path.write_bytes(data)
    return {"deepchecks": version, "adaptation": "stdlib-metadata-packaging-v1",
            "files": records, "status": "PASS"}


def main():
    package = metadata.distribution("deepchecks")
    result = prepare(package.locate_file("deepchecks"), package.version)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
