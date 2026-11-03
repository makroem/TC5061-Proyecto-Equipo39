"""Rutas de despliegue; no contiene credenciales ni configura el Registry."""

from dataclasses import dataclass
import os
from pathlib import Path

from mibici_equipo39 import config as C

MODEL_NAME = "mibici-equipo39-p1-demanda"
MODEL_ALIAS = C.MODEL_ALIAS
MAX_BATCH_SIZE = 100
DEFAULT_MODEL_DIR = C.MODELS / "serving" / "p1"
DEFAULT_MANIFEST = C.REFERENCES / "etapa4" / "model_manifest.json"


@dataclass(frozen=True)
class Settings:
    model_dir: Path
    model_manifest: Path

    @classmethod
    def from_env(cls):
        """El contenedor fija MODEL_DIR=/app/model; localmente usa models/serving/p1."""
        return cls(
            Path(os.environ.get("MODEL_DIR", DEFAULT_MODEL_DIR)),
            Path(os.environ.get("MODEL_MANIFEST", DEFAULT_MANIFEST)),
        )
