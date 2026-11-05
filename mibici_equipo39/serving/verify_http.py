"""Comprueba una API en ejecución contra el paquete P1 local aprobado."""

import argparse
from datetime import datetime, timezone
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .model_loader import load_model, verify_bundle
from .settings import DEFAULT_MANIFEST, DEFAULT_MODEL_DIR


def verify_http(url, model_dir, manifest_path):
    url = url.rstrip('/')
    loaded = load_model(model_dir, manifest_path)
    rows = [{'station_id': station, 'hour_of_day': hour, 'day_of_week': 5,
             'month': 6, 'is_weekend': 1,
             'hour_sin': math.sin(2 * math.pi * hour / 24),
             'hour_cos': math.cos(2 * math.pi * hour / 24),
             'month_sin': math.sin(math.pi), 'month_cos': math.cos(math.pi)}
            for station in ('10', '20', '99999') for hour in range(24)]
    frame = pd.DataFrame(rows).astype({'station_id': 'object', 'hour_of_day': 'int32',
        'day_of_week': 'int32', 'month': 'int32', 'is_weekend': 'int64',
        'hour_sin': 'float64', 'hour_cos': 'float64', 'month_sin': 'float64', 'month_cos': 'float64'})
    expected = np.asarray(loaded.predict(frame), dtype=float)
    status = {}
    for endpoint in ('/health', '/ready', '/docs'):
        response = requests.get(url + endpoint, timeout=(5, 30))
        response.raise_for_status()
        status[endpoint] = response.status_code
    response = requests.post(url + '/predict', json={'instances': rows}, timeout=(5, 30))
    response.raise_for_status()
    body = response.json()
    for public, internal in [('model_name', 'model_name'), ('model_version', 'model_version'),
                             ('model_bundle_sha256', 'bundle_sha256')]:
        if body.get(public) != str(loaded.manifest[internal]):
            raise ValueError('La API no identifica el paquete esperado.')
    predictions = body['predictions']
    if [row['station_id'] for row in predictions] != frame.station_id.tolist():
        raise ValueError('La respuesta cambió el orden o el número de entradas.')
    values = np.asarray([row['predicted_trips'] for row in predictions], dtype=float)
    if not np.isfinite(values).all() or not np.allclose(values, expected, atol=1e-12, rtol=0):
        raise ValueError('Las predicciones HTTP difieren del paquete local.')
    repeated = requests.post(url + '/predict', json={'instances': rows}, timeout=(5, 30))
    repeated.raise_for_status()
    if repeated.json() != body:
        raise ValueError('La repetición no produjo la misma respuesta.')
    for invalid in [{'instances': []}, {'instances': [{**rows[0], 'hour_of_day': 24}]}]:
        if requests.post(url + '/predict', json=invalid, timeout=(5, 30)).status_code != 422:
            raise ValueError('La API aceptó una entrada inválida.')
    verify_bundle(model_dir, loaded.manifest)
    return {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'transport': 'HTTP',
            'service_url': url, 'rows': len(rows), 'status_codes': status,
            'invalid_inputs_status': 422, 'repeat_identical': True,
            'max_abs_difference': float(np.max(np.abs(values - expected))),
            'model_name': body['model_name'], 'model_version': body['model_version'],
            'bundle_sha256': body['model_bundle_sha256'], 'bundle_unchanged': True,
            'example': {'input': rows[0], 'output': predictions[0]},
            'scope': 'HTTP against local package; container execution requires engine evidence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--model-dir', type=Path, default=DEFAULT_MODEL_DIR)
    parser.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument('--output', type=Path, default=Path('private_results/http_check.json'))
    args = parser.parse_args()
    result = verify_http(args.url, args.model_dir, args.manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
