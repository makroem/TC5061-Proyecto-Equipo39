"""Validación de entradas, contrato HTTP y carga única, sin acceder al Registry."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from fastapi.testclient import TestClient
import numpy as np
from pydantic import ValidationError
import pytest

from mibici_equipo39.serving.app import create_app
from mibici_equipo39.serving.predictor import to_frame
from mibici_equipo39.serving.schemas import PredictionRequest


@pytest.fixture
def payload():
    return json.loads((Path(__file__).resolve().parents[2] /
        'references/etapa4/examples/predict_request.json').read_text(encoding='utf-8-sig'))


@pytest.fixture
def loaded():
    return SimpleNamespace(manifest={'model_name': 'fixture-p1', 'model_version': '1',
        'bundle_sha256': 'a' * 64}, predict=Mock(side_effect=lambda frame: np.full(len(frame), 2.5)))


def test_exact_model_types_and_order(payload):
    payload['instances'].append({**payload['instances'][0], 'station_id': '20'})
    frame = to_frame(PredictionRequest.model_validate(payload))
    assert frame.station_id.tolist() == ['10', '20']
    assert str(frame.station_id.dtype) == 'object'
    for name in ['hour_of_day', 'day_of_week', 'month']:
        assert str(frame[name].dtype) == 'int32'
    assert str(frame.is_weekend.dtype) == 'int64'
    for name in ['hour_sin', 'hour_cos', 'month_sin', 'month_cos']:
        assert str(frame[name].dtype) == 'float64'


@pytest.mark.parametrize('field,value', [
    ('station_id', 10), ('station_id', ''), ('station_id', ' 10'), ('station_id', '../10'),
    ('hour_of_day', -1), ('hour_of_day', 24), ('hour_of_day', '6'), ('hour_of_day', True),
    ('day_of_week', 7), ('day_of_week', -1), ('month', 0), ('month', 13),
    ('is_weekend', 2), ('is_weekend', True), ('is_weekend', 1),
    ('hour_sin', float('nan')), ('month_cos', float('inf')), ('hour_cos', 0.1),
    ('month_sin', -0.5), ('month_cos', True), ('hour_cos', '0'),
])
def test_bad_values_rejected(payload, field, value):
    payload['instances'][0][field] = value
    with pytest.raises(ValidationError):
        PredictionRequest.model_validate(payload)


@pytest.mark.parametrize('count,valid', [(0, False), (1, True), (100, True), (101, False)])
def test_batch_boundaries(payload, count, valid):
    payload['instances'] = payload['instances'] * count
    if valid:
        assert len(PredictionRequest.model_validate(payload).instances) == count
    else:
        with pytest.raises(ValidationError):
            PredictionRequest.model_validate(payload)


def test_missing_and_extra_fields_rejected(payload):
    missing = copy.deepcopy(payload)
    del missing['instances'][0]['month']
    extra = copy.deepcopy(payload)
    extra['instances'][0]['model_uri'] = 'untrusted'
    for body in [missing, extra, {**payload, 'extra': 1}]:
        with pytest.raises(ValidationError):
            PredictionRequest.model_validate(body)


def test_rounded_cyclic_inputs_and_unknown_station_accepted(payload):
    payload['instances'][0]['station_id'] = '99999'
    payload['instances'][0]['month_cos'] = 0.866025
    assert PredictionRequest.model_validate(payload).instances[0].station_id == '99999'


def test_http_contract_loads_once_and_returns_lineage(payload, loaded):
    loader = Mock(return_value=loaded)
    with TestClient(create_app(model_loader=loader)) as client:
        assert client.get('/health').json() == {'status': 'ok'}
        assert client.get('/ready').status_code == 200
        assert client.get('/docs').status_code == 200
        assert '/predict' in client.get('/openapi.json').json()['paths']
        for _ in range(2):
            response = client.post('/predict', json=payload)
            assert response.status_code == 200
            assert response.json() == {'model_name': 'fixture-p1', 'model_version': '1',
                'model_bundle_sha256': 'a' * 64,
                'predictions': [{'station_id': '10', 'predicted_trips': 2.5}]}
        assert loader.call_count == 1
    assert loaded.predict.call_count == 2


def test_http_preserves_batch_order(payload, loaded):
    payload['instances'] *= 3
    payload['instances'] = [{**row, 'station_id': station}
                           for row, station in zip(payload['instances'], ['20', '10', '99999'])]
    loaded.predict.side_effect = lambda frame: np.array([2.5, 1.25, 0.0])
    with TestClient(create_app(model_loader=lambda *_: loaded)) as client:
        out = client.post('/predict', json=payload).json()['predictions']
    assert [x['station_id'] for x in out] == ['20', '10', '99999']
    assert [x['predicted_trips'] for x in out] == [2.5, 1.25, 0.0]


def test_not_ready_is_safe(payload):
    def broken(*_):
        raise OSError('private-path-and-secret')
    with TestClient(create_app(model_loader=broken)) as client:
        assert client.get('/health').status_code == 200
        for response in [client.get('/ready'), client.post('/predict', json=payload)]:
            assert response.status_code == 503
            assert 'private-path' not in response.text


@pytest.mark.parametrize('output', [np.array([float('nan')]), np.array([-1]), np.array([]), np.array([[2.5]])])
def test_invalid_model_output_is_not_exposed(payload, loaded, output):
    loaded.predict.side_effect = lambda frame: output
    with TestClient(create_app(model_loader=lambda *_: loaded)) as client:
        response = client.post('/predict', json=payload)
        assert response.status_code == 500
        assert response.json()['detail'] == 'No se pudo completar la prediccion.'


def test_exception_is_not_exposed(payload, loaded):
    loaded.predict.side_effect = RuntimeError('private-path-and-secret')
    with TestClient(create_app(model_loader=lambda *_: loaded)) as client:
        response = client.post('/predict', json=payload)
        assert response.status_code == 500
        assert 'private-path' not in response.text


def test_http_invalid_json_and_nonfinite_are_422(payload, loaded):
    with TestClient(create_app(model_loader=lambda *_: loaded)) as client:
        for text in ['{', json.dumps({'instances': []}),
                     json.dumps({'instances': [{**payload['instances'][0], 'hour_sin': float('nan')}]}),
                     json.dumps({'instances': [{**payload['instances'][0], 'extra': 'private-body'}]})]:
            response = client.post('/predict', content=text, headers={'Content-Type': 'application/json'})
            assert response.status_code == 422
            assert 'private-body' not in response.text
        assert loaded.predict.call_count == 0
