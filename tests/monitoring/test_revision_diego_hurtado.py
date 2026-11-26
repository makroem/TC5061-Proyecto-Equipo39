"""Revision independiente de integridad del manifiesto - Diego Hurtado, #83."""

import json

import pytest

from mibici_equipo39.monitoring import seasonal


def approved_manifest():
    """Construye una referencia con el linaje aprobado."""
    config = seasonal.load_config()

    model = json.loads(
        (
            seasonal.ROOT
            / "references/etapa4/model_manifest.json"
        ).read_text(encoding="utf-8")
    )

    return {
        "protocol_sha256": config["protocol_sha256"],
        "bundle_sha256": model["bundle_sha256"],
        "source_run_id": config["expected_a_run"],
        "model_version": config["expected_a_version"],
        "files": {},
    }


def stop_after_lineage(*args, **kwargs):
    """Evita cargar datos reales tras superar el control."""
    raise RuntimeError("CONTROL: linaje valido")


@pytest.mark.parametrize(
    "field, invalid_value",
    [
        ("model_version", "VERSION_ALTERADA"),
        ("bundle_sha256", "0" * 64),
    ],
)
def test_rejects_tampered_manifest(
    tmp_path, monkeypatch, field, invalid_value
):
    manifest = approved_manifest()

    prediction_dir = tmp_path / "predictions"
    prediction_dir.mkdir()
    report_dir = tmp_path / "reports"
    manifest_path = prediction_dir / "manifest.json"

    monkeypatch.setattr(
        seasonal, "verified_dataset", stop_after_lineage
    )

    # Control positivo: el linaje aprobado supera
    # la primera validacion.
    manifest_path.write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(RuntimeError, match="CONTROL: linaje valido"):
        seasonal.generate(prediction_dir, report_dir)

    # Control negativo: alteracion aislada del manifiesto.
    corrupted = {**manifest, field: invalid_value}

    manifest_path.write_text(
        json.dumps(corrupted), encoding="utf-8"
    )

    with pytest.raises(
        ValueError,
        match="Linaje de predicciones distinto",
    ):
        seasonal.generate(prediction_dir, report_dir)
