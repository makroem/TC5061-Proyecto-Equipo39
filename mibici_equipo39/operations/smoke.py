"""Comprobación HTTP del contrato, identidad del modelo y respuesta de error."""
import argparse
import json
import urllib.error
import urllib.request
from pathlib import Path
from .payload import make_payload, valid_response

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def check(url, manifest_path):
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf8'))
    def get(path):
        with urllib.request.urlopen(url.rstrip('/')+path, timeout=15) as response:
            return json.load(response)
    require(get('/health')['status'] == 'ok', 'Salud inválida')
    ready = get('/ready')
    require(ready['model_bundle_sha256'] == manifest['bundle_sha256'], 'Huella de modelo distinta')
    require(ready['model_name'] == manifest['model_name'], 'Nombre de modelo distinto')
    require(ready['model_version'] == str(manifest['model_version']), 'Versión de modelo distinta')
    for size in (1, 10, 100):
        request = urllib.request.Request(url.rstrip('/')+'/predict', data=json.dumps(make_payload(size, 39)).encode(),
                                         headers={'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.load(response)
        require(valid_response(body, size), 'Contrato de respuesta inválido')
        require(body['model_bundle_sha256'] == manifest['bundle_sha256'], 'Huella de predicción distinta')
    request = urllib.request.Request(url.rstrip('/')+'/predict', data=b'{"instances":[]}',
                                     headers={'Content-Type': 'application/json'}, method='POST')
    try:
        urllib.request.urlopen(request, timeout=15)
    except urllib.error.HTTPError as error:
        require(error.code == 422, 'Código de rechazo distinto de 422')
    else:
        raise AssertionError('Una solicitud vacía debe rechazarse.')
    return {'status': 'passed', 'model_name': ready['model_name'], 'model_version': ready['model_version'],
            'model_bundle_sha256': ready['model_bundle_sha256'], 'valid_batches': [1, 10, 100], 'invalid_status': 422}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://127.0.0.1:8006')
    parser.add_argument('--manifest', default='references/etapa4/model_manifest.json')
    parser.add_argument('--output')
    args = parser.parse_args()
    result = check(args.url, args.manifest)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result))
