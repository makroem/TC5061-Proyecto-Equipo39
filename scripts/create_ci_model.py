"""Crea una fixture serializada solo para CI; no sustituye ni publica P1."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models import Model, ModelSignature
from sklearn.dummy import DummyRegressor
from mibici_equipo39.operations.payload import make_payload
from mibici_equipo39.serving.model_loader import inventory, bundle_digest

folder = Path('private_results/etapa6/ci').resolve()
folder.mkdir(parents=True, exist_ok=True)
model_path = folder / 'model'
if model_path.exists():
    raise SystemExit('La fixture ya existe; usar una carpeta de trabajo limpia.')
official = json.loads(Path('references/etapa4/model_manifest.json').read_text(encoding='utf8'))
frame = pd.DataFrame(make_payload(4, 39)['instances'])
for name in ('hour_of_day', 'day_of_week', 'month'):
    frame[name] = frame[name].astype('int32')
frame['is_weekend'] = frame['is_weekend'].astype('int64')
model = DummyRegressor(strategy='constant', constant=1.0).fit(frame, [1.0]*4)
os.environ['MLFLOW_ALLOW_FILE_STORE'] = 'true'
mlflow.set_tracking_uri((folder/'fixture_runs').as_uri())
mlflow.set_experiment('ci-fixture-only')
with mlflow.start_run(tags={'purpose': 'fixture de contrato; no es P1 oficial'}) as run:
    mlflow.sklearn.save_model(model, str(model_path), signature=ModelSignature.from_dict(official['signature']),
                             input_example=frame.head(1), serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_CLOUDPICKLE, pip_requirements=['scikit-learn==1.6.1'])
    metadata = Model.load(str(model_path/'MLmodel'))
    metadata.run_id = run.info.run_id
    metadata.save(str(model_path/'MLmodel'))
commit = os.environ.get('GITHUB_SHA') or subprocess.check_output(
    ['git', '-c', 'safe.directory='+Path.cwd().as_posix(), 'rev-parse', 'HEAD'], text=True).strip()
files = inventory(model_path)
manifest = dict(schema_version=1, model_name='ci-fixture-only', model_version='1',
                source_run_id=run.info.run_id, training_commit=commit,
                data_version=hashlib.sha256(frame.to_json().encode()).hexdigest(),
                signature=official['signature'], files=files, bundle_sha256=bundle_digest(files),
                purpose='Prueba de infraestructura; no es el modelo oficial ni una métrica de desempeño.')
(folder/'model_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
print('Fixture de CI preparada; el paquete oficial no se utiliza ni se publica.')
