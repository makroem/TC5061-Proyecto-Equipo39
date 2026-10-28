"""Comprueba HTTPS y configuración con valores sintéticos; no guarda CSV ni secretos."""

import argparse
import hashlib
from importlib.metadata import version
from io import StringIO
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit

import certifi
from dotenv import dotenv_values, load_dotenv
import requests

from mibici_equipo39 import config as C
from mibici_equipo39.dataset import DOWNLOAD_HEADERS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=Path("private_quality/dependency_update/compatibility.json"))
    args = parser.parse_args()
    result = {"scope": "HTTPS del catálogo y configuración sintética",
              "python": sys.version.split()[0],
              "versions": {name: version(name) for name in
                           ["certifi", "requests", "pytest", "python-dotenv", "mlflow", "pyarrow"]}}

    # La consulta es de lectura, usa el catálogo configurado y verifica el certificado.
    if urlsplit(C.STATIONS_URL).scheme != "https":
        raise ValueError("La fuente del catálogo debe utilizar HTTPS.")
    with requests.get(C.STATIONS_URL, headers=DOWNLOAD_HEADERS, stream=True,
                      verify=certifi.where(), timeout=(10, 30)) as response:
        response.raise_for_status()
        if urlsplit(response.url).scheme != "https":
            raise ValueError("La fuente redirigió a una conexión sin HTTPS.")
        sample = next(response.iter_content(1024), b"")
        if not sample or b"<html" in sample.lower() or b"<!doctype" in sample.lower():
            raise ValueError("La fuente no devolvió un inicio de archivo válido.")
        result["https"] = {"status": "PASS", "http_status": response.status_code,
                           "host": urlsplit(response.url).hostname,
                           "tls_verification": True, "sample_bytes": len(sample),
                           "ca_bundle_sha256": hashlib.sha256(Path(certifi.where()).read_bytes()).hexdigest()}

    # No leer archivos .env de la máquina ni publicar sus valores.
    key = "MIBICI_A7_SYNTHETIC_CONFIG_CHECK"
    existed, previous = key in os.environ, os.environ.get(key)
    try:
        parsed = dotenv_values(stream=StringIO("A7_NUMBER=39\nA7_TEXT='equipo de prueba'\n"),
                               interpolate=False)
        if parsed != {"A7_NUMBER": "39", "A7_TEXT": "equipo de prueba"}:
            raise RuntimeError("No se conservó la configuración sintética.")
        os.environ[key] = "existing_synthetic_value"
        load_dotenv(stream=StringIO(f"{key}=replacement_synthetic_value\n"),
                    override=False, interpolate=False)
        if os.environ[key] != "existing_synthetic_value":
            raise RuntimeError("Se sobrescribió una variable sin autorización.")
        result["dotenv"] = {"status": "PASS", "synthetic_parse": True,
                            "existing_environment_preserved": True}
    finally:
        if existed:
            os.environ[key] = previous
        else:
            os.environ.pop(key, None)

    result["status"] = "PASS"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
