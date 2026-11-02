"""La preparación del entorno rechaza código inesperado y puede repetirse."""

import importlib.util
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "prepare_deepchecks.py"
spec = importlib.util.spec_from_file_location("prepare_deepchecks", SCRIPT)
prep = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prep)


@pytest.fixture
def package(tmp_path, monkeypatch):
    # Archivos mínimos: las mismas expresiones de importación del paquete real.
    patches = {}
    for relative, entry in prep.PATCHES.items():
        content = "\n".join(old for old, _ in entry["replacements"]).encode()
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        patches[relative] = dict(entry, sha256=prep.digest(content))
    monkeypatch.setattr(prep, "PATCHES", patches)
    return tmp_path


def test_prepare_is_idempotent(package):
    first = prep.prepare(package, "0.19.1")
    assert all(item["changed"] for item in first["files"])
    second = prep.prepare(package, "0.19.1")
    assert not any(item["changed"] for item in second["files"])
    assert [r["adapted_sha256"] for r in first["files"]] == [
        r["adapted_sha256"] for r in second["files"]]


def test_unknown_version_does_not_write(package):
    before = {p: p.read_bytes() for p in package.rglob("*.py")}
    with pytest.raises(ValueError, match="0.19.1"):
        prep.prepare(package, "0.20.0")
    assert all(p.read_bytes() == data for p, data in before.items())


def test_both_files_are_checked_before_writing(package):
    first = package / "utils/display.py"
    before = first.read_bytes()
    second = package / "core/serialization/dataframe/html.py"
    second.write_bytes(second.read_bytes() + b"\n# cambio inesperado")
    with pytest.raises(ValueError, match="distinto"):
        prep.prepare(package, "0.19.1")
    assert first.read_bytes() == before


def test_missing_file_does_not_write(package):
    first = package / "utils/display.py"
    before = first.read_bytes()
    (package / "core/serialization/dataframe/html.py").unlink()
    with pytest.raises(FileNotFoundError):
        prep.prepare(package, "0.19.1")
    assert first.read_bytes() == before


def test_modified_adaptation_is_rejected(package):
    prep.prepare(package, "0.19.1")
    first = package / "utils/display.py"
    first.write_bytes(first.read_bytes() + b"\n# cambio posterior")
    with pytest.raises(ValueError, match="distinto"):
        prep.prepare(package, "0.19.1")


@pytest.mark.parametrize("original", [b"", b"x\nx"])
def test_replacement_must_be_unique(original):
    with pytest.raises(ValueError, match="exactamente una"):
        prep.adapted_bytes(original, [("x", "y")])
