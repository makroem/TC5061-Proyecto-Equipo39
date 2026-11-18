"""Solicitudes sintéticas válidas; no utiliza registros de personas ni viajes."""
import math
import random


def make_payload(batch_size=1, seed=None):
    if not isinstance(batch_size, int) or isinstance(batch_size, bool) or not 1 <= batch_size <= 100:
        raise ValueError('El lote debe contener entre 1 y 100 filas.')
    rng = random.Random(seed)
    rows = []
    for _ in range(batch_size):
        hour, day, month = rng.randrange(24), rng.randrange(7), rng.randrange(1, 13)
        rows.append(dict(station_id=rng.choice(['10', '35', '100']), hour_of_day=hour,
                         day_of_week=day, month=month, is_weekend=int(day >= 5),
                         hour_sin=math.sin(2*math.pi*hour/24), hour_cos=math.cos(2*math.pi*hour/24),
                         month_sin=math.sin(2*math.pi*month/12), month_cos=math.cos(2*math.pi*month/12)))
    return {'instances': rows}


def valid_response(response, expected_count):
    if not isinstance(response, dict) or not isinstance(response.get('predictions'), list):
        return False
    if len(response['predictions']) != expected_count:
        return False
    for row in response['predictions']:
        value = row.get('predicted_trips') if isinstance(row, dict) else None
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
            return False
    return all(response.get(key) for key in ('model_name', 'model_version', 'model_bundle_sha256'))
