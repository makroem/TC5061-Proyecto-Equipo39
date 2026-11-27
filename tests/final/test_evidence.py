"""Casos de pérdida, alteración y rutas inválidas del inventario histórico."""

import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.check_final_evidence import verify


class EvidenceTests(unittest.TestCase):
    def test_original_and_changed_file(self):
        with TemporaryDirectory() as folder:
            path = Path(folder) / "measurement.csv"
            path.write_bytes(b"value\n1.25\n")
            manifest = {"files": {path.name: hashlib.sha256(path.read_bytes()).hexdigest()}}
            self.assertTrue(verify(folder, manifest)["ok"])
            crlf = b"value\r\n1.25\r\n"
            manifest["files"][path.name] = [manifest["files"][path.name], hashlib.sha256(crlf).hexdigest()]
            path.write_bytes(crlf)
            self.assertTrue(verify(folder, manifest)["ok"])
            path.write_bytes(b"value\n1.20\n")
            self.assertEqual(verify(folder, manifest)["failures"][0]["reason"], "sha256_mismatch")

    def test_missing_file(self):
        with TemporaryDirectory() as folder:
            result = verify(folder, {"files": {"missing.csv": "0" * 64}})
            self.assertFalse(result["ok"])
            self.assertEqual(result["failures"][0]["reason"], "missing")

    def test_outside_path_is_rejected(self):
        with TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                verify(folder, {"files": {"../outside.txt": "0" * 64}})

    def test_empty_inventory_is_rejected(self):
        with self.assertRaises(ValueError):
            verify(".", {"files": {}})


if __name__ == "__main__":
    unittest.main()
