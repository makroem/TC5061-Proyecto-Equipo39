"""Contrato público de P1; los tipos y las variables conservan la firma registrada."""

import math
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .settings import MAX_BATCH_SIZE

CYCLIC_TOLERANCE = 1e-6


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)


class PredictionInput(StrictModel):
    station_id: Annotated[str, Field(pattern=r'^[1-9][0-9]{0,5}$')]
    hour_of_day: Annotated[int, Field(ge=0, le=23)]
    day_of_week: Annotated[int, Field(ge=0, le=6)]
    month: Annotated[int, Field(ge=1, le=12)]
    is_weekend: Annotated[int, Field(ge=0, le=1)]
    hour_sin: Annotated[float, Field(ge=-1, le=1)]
    hour_cos: Annotated[float, Field(ge=-1, le=1)]
    month_sin: Annotated[float, Field(ge=-1, le=1)]
    month_cos: Annotated[float, Field(ge=-1, le=1)]

    @model_validator(mode='after')
    def calendar_is_consistent(self):
        if self.is_weekend != int(self.day_of_week >= 5):
            raise ValueError('is_weekend debe coincidir con day_of_week (lunes=0).')
        expected = {
            'hour_sin': math.sin(2 * math.pi * self.hour_of_day / 24),
            'hour_cos': math.cos(2 * math.pi * self.hour_of_day / 24),
            'month_sin': math.sin(2 * math.pi * self.month / 12),
            'month_cos': math.cos(2 * math.pi * self.month / 12),
        }
        if any(abs(getattr(self, key) - value) > CYCLIC_TOLERANCE
               for key, value in expected.items()):
            raise ValueError('Variables ciclicas inconsistentes; tolerancia absoluta 1e-6.')
        return self


class PredictionRequest(StrictModel):
    model_config = ConfigDict(json_schema_extra={"examples": [{'instances': [{'station_id': '10', 'hour_of_day': 6, 'day_of_week': 0, 'month': 1, 'is_weekend': 0, 'hour_sin': 1.0, 'hour_cos': 0.0, 'month_sin': 0.5, 'month_cos': 0.8660254037844386}]}]})
    instances: Annotated[list[PredictionInput], Field(min_length=1, max_length=MAX_BATCH_SIZE)]


class Prediction(StrictModel):
    station_id: str
    predicted_trips: Annotated[float, Field(ge=0)]


class PredictionResponse(StrictModel):
    model_name: str
    model_version: str
    model_bundle_sha256: str
    predictions: list[Prediction]


class ValidationIssue(StrictModel):
    loc: list[str | int]
    msg: str
    type: str


class ValidationResponse(StrictModel):
    detail: list[ValidationIssue]


class ServiceError(StrictModel):
    detail: str
