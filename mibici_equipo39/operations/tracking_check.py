"""Escribe y recupera una evidencia mínima para comprobar persistencia."""
import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4

def request(url, path, data=None):
    body=None if data is None else json.dumps(data).encode()
    with urlopen(Request(url+path, data=body, headers={'Content-Type':'application/json'}), timeout=20) as response:
        return json.load(response)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['write','read'])
    parser.add_argument('--url',default='http://127.0.0.1:5006')
    parser.add_argument('--record',default='private_results/etapa6/tracking_check.json')
    args=parser.parse_args()
    record=Path(args.record)
    if args.action=='write':
        result=request(args.url,'/api/2.0/mlflow/experiments/create',{'name':'etapa6-persistencia-'+uuid4().hex})
        record.parent.mkdir(parents=True,exist_ok=True)
        record.write_text(json.dumps(result),encoding='utf8')
        print('Registro de comprobación creado.')
    else:
        expected=json.loads(record.read_text(encoding='utf8'))['experiment_id']
        actual=request(args.url,'/api/2.0/mlflow/experiments/get?experiment_id='+expected)
        if actual['experiment']['experiment_id']!=expected:
            raise RuntimeError('El registro persistente no coincide.')
        print('Persistencia verificada después de recrear el servicio.')
