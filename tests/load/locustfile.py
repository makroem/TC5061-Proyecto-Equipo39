"""Carga válida 80% individual y 20% lotes de diez; registra inferencias útiles."""
import json
import os
import time
from pathlib import Path
from locust import HttpUser, between, events, task
from mibici_equipo39.operations.payload import make_payload, valid_response

COUNTS = {'successful_requests': 0, 'successful_predictions': 0}
START = None

@events.test_start.add_listener
def start(environment, **kwargs):
    global START
    START = time.time()
    COUNTS.update(successful_requests=0, successful_predictions=0)

@events.quitting.add_listener
def finish(environment, **kwargs):
    end = time.time()
    total = environment.stats.total
    result = dict(COUNTS, start_epoch=START, end_epoch=end, duration_seconds=end-START,
                  requests=total.num_requests, failures=total.num_failures,
                  failure_ratio=total.fail_ratio, latency_p50_ms=total.get_response_time_percentile(.5),
                  latency_p95_ms=total.get_response_time_percentile(.95),
                  latency_p99_ms=total.get_response_time_percentile(.99),
                  model_name=os.environ.get('EXPECTED_MODEL_NAME', 'mibici-equipo39-p1-demanda'),
                  request_mix='80% una fila; 20% diez filas; pesos de tareas, proporción observada variable')
    destination = os.environ.get('LOAD_SUMMARY')
    if destination:
        Path(destination).parent.mkdir(parents=True, exist_ok=True)
        Path(destination).write_text(json.dumps(result, indent=2), encoding='utf8')
    if total.num_requests == 0 or total.fail_ratio > .001:
        environment.process_exit_code = 1

class MiBiciUser(HttpUser):
    wait_time = between(.1, .5)

    def predict(self, size):
        with self.client.post('/predict', json=make_payload(size), name=f'/predict lote={size}',
                              catch_response=True, timeout=10) as response:
            try:
                body = response.json()
            except ValueError:
                response.failure('Respuesta no JSON')
                return
            if response.status_code != 200 or not valid_response(body, size):
                response.failure('Contrato de predicción inválido')
                return
            if (body['model_name'] != os.environ.get('EXPECTED_MODEL_NAME', 'mibici-equipo39-p1-demanda')
                or str(body['model_version']) != os.environ.get('EXPECTED_MODEL_VERSION', '1')
                or (os.environ.get('EXPECTED_BUNDLE_SHA256') and body['model_bundle_sha256'] != os.environ['EXPECTED_BUNDLE_SHA256'])):
                response.failure('Modelo distinto del esperado')
                return
            COUNTS['successful_requests'] += 1
            COUNTS['successful_predictions'] += size
            response.success()

    @task(4)
    def individual(self):
        self.predict(1)

    @task(1)
    def batch(self):
        self.predict(10)
