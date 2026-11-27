"""Comprueba que las evidencias históricas conservan sus huellas originales."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root, manifest):
    root = Path(root).resolve()
    entries = manifest.get("files")
    if not isinstance(entries, dict) or not entries:
        raise ValueError("El inventario no contiene archivos.")
    failures = []
    for relative, expected in entries.items():
        path = (root / relative).resolve()
        if Path(relative).is_absolute() or not path.is_relative_to(root):
            raise ValueError("Ruta fuera del repositorio.")
        if not path.is_file():
            failures.append({"path": relative, "reason": "missing"})
        elif hashlib.sha256(path.read_bytes()).hexdigest() not in (
            expected if isinstance(expected, list) else [expected]
        ):
            failures.append({"path": relative, "reason": "sha256_mismatch"})
    return {"checked": len(entries), "ok": not failures, "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path,
                        default=ROOT / "references/etapa7/baseline_sha256.json")
    args = parser.parse_args()
    result = verify(ROOT, json.loads(args.manifest.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
