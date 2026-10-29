"""Compara valores y esquema de tablas Parquet sin publicar sus filas.

Ejecutar con ambos entornos sobre los mismos archivos. --roundtrip escribe una
copia nueva con el PyArrow instalado; nunca sobrescribe la entrada.
"""
import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


def inspect_file(path, destination=None):
    parquet = pq.ParquetFile(path)
    h = hashlib.sha256()
    rows, nulls, dtypes = 0, None, None
    writer = pq.ParquetWriter(destination, parquet.schema_arrow) if destination else None
    try:
        for batch in parquet.iter_batches(batch_size=65536):
            frame = batch.to_pandas()
            current = {c: str(t) for c, t in frame.dtypes.items()}
            if dtypes is not None and dtypes != current:
                raise ValueError("Cambió el esquema entre bloques.")
            dtypes = current
            counts = frame.isna().sum()
            nulls = counts if nulls is None else nulls.add(counts)
            h.update(pd.util.hash_pandas_object(frame, index=False).to_numpy(dtype="<u8").tobytes())
            rows += len(frame)
            if writer:
                writer.write_batch(batch)
    finally:
        if writer:
            writer.close()
    return {"rows": rows, "columns": parquet.schema_arrow.names, "dtypes": dtypes,
            "nulls": {k: int(v) for k, v in nulls.items()} if nulls is not None else {},
            "row_hash_sha256": h.hexdigest()}


def check(input_folder, output, roundtrip=None, compare=None):
    source = input_folder.resolve()
    files = sorted(source.glob("*.parquet"))
    if not files:
        raise ValueError("No hay tablas Parquet en la carpeta indicada.")
    if roundtrip:
        roundtrip = roundtrip.resolve()
        if roundtrip.exists() or source == roundtrip or source in roundtrip.parents or roundtrip in source.parents:
            raise ValueError("La carpeta de copias debe ser nueva y ajena a la entrada.")
        roundtrip.mkdir(parents=True, exist_ok=False)
    results = {p.name: inspect_file(p, roundtrip / p.name if roundtrip else None) for p in files}
    if compare:
        expected = json.loads(compare.read_text(encoding="utf-8"))["tables"]
        if results != expected:
            raise ValueError("Los valores, conteos, nulos o tipos difieren de la referencia.")
    if roundtrip:
        restored = {p.name: inspect_file(roundtrip / p.name) for p in files}
        if restored != results:
            raise ValueError("La escritura y relectura cambió el contenido lógico.")
    payload = {"status": "PASS", "pyarrow": pa.__version__, "pandas": pd.__version__,
               "comparison_performed": compare is not None, "roundtrip_performed": roundtrip is not None,
               "hash_method": "SHA256 de hashes de filas pandas uint64 little-endian, orden original, sin índice",
               "tables": results}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {"status": "PASS", "tables": len(results), "pyarrow": pa.__version__}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--roundtrip", type=Path)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.input, args.output, args.roundtrip, args.compare)))
