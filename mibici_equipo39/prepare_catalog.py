"""Recupera solamente el catálogo histórico y comprueba su versión antes de la ingesta."""

import argparse
import json

from . import config as C
from .dataset import clean_stations, download_file, sha_file


def prepare_catalog():
    manifest = json.loads((C.REFERENCES / "data_manifest.json").read_text(encoding="utf-8"))
    source = next(item for item in manifest["sources"] if item["url"] == C.STATIONS_URL)
    path = C.EXTERNAL / source["name"]
    origin = download_file(C.STATIONS_URL, path, source["sha256"],
                           cache_dir=C.SOURCE_CACHE_DIR, backup_url=C.STATIONS_BACKUP_URL)
    stations, encoding, separator = clean_stations(path)
    if len(stations) != source["rows"] or path.stat().st_size != source["bytes"]:
        raise ValueError("El catálogo no coincide con el tamaño y las filas del manifiesto.")
    return {"source_name": path.name, "retrieval": origin, "sha256": sha_file(path),
            "bytes": path.stat().st_size, "rows": len(stations),
            "encoding": encoding, "separator": separator, "matches_manifest": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(prepare_catalog(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
