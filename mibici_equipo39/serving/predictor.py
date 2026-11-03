"""Conversión de solicitudes validadas a los tipos exactos del modelo registrado."""

import numpy as np
import pandas as pd

from .schemas import Prediction, PredictionRequest, PredictionResponse

INPUT_TYPES = {
    'station_id': 'object', 'hour_of_day': 'int32', 'day_of_week': 'int32',
    'month': 'int32', 'is_weekend': 'int64', 'hour_sin': 'float64',
    'hour_cos': 'float64', 'month_sin': 'float64', 'month_cos': 'float64',
}


def to_frame(request: PredictionRequest):
    return pd.DataFrame([row.model_dump() for row in request.instances],
                        columns=list(INPUT_TYPES)).astype(INPUT_TYPES)


def predict_request(loaded, request: PredictionRequest):
    values = np.asarray(loaded.predict(to_frame(request)), dtype=float)
    if values.shape != (len(request.instances),) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('El modelo produjo una salida incompatible con el contrato.')
    return PredictionResponse(
        model_name=loaded.manifest['model_name'],
        model_version=str(loaded.manifest['model_version']),
        model_bundle_sha256=loaded.manifest['bundle_sha256'],
        predictions=[Prediction(station_id=row.station_id, predicted_trips=float(value))
                     for row, value in zip(request.instances, values)],
    )
