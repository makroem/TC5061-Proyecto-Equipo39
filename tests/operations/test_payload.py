import pytest
from mibici_equipo39.operations.payload import make_payload, valid_response
from mibici_equipo39.serving.schemas import PredictionRequest

@pytest.mark.parametrize('size', [1, 10, 100])
def test_requests_respect_real_api_contract(size):
    body = make_payload(size, 39)
    assert len(PredictionRequest.model_validate(body).instances) == size
    assert body == make_payload(size, 39)

@pytest.mark.parametrize('size', [0, 101, -1, True, 1.5])
def test_invalid_load_sizes_rejected(size):
    with pytest.raises(ValueError):
        make_payload(size)

@pytest.mark.parametrize('value', [-1, float('nan'), float('inf'), True, '1'])
def test_invalid_predictions_cannot_count_as_success(value):
    body = dict(model_name='test', model_version='1', model_bundle_sha256='digest',
                predictions=[{'predicted_trips': value}])
    assert not valid_response(body, 1)

def test_incomplete_batch_cannot_count_as_success():
    body = dict(model_name='test', model_version='1', model_bundle_sha256='digest',
                predictions=[{'predicted_trips': 1.0}])
    assert valid_response(body, 1)
    assert not valid_response(body, 10)
