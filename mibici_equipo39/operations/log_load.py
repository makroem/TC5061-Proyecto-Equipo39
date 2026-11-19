"""Registra métricas observadas de carga en el tracking operativo."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import time
from .http_client import HTTPStatusError, json_request

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--input",default="references/etapa6/mediciones_marco")
    parser.add_argument("--url",default="http://127.0.0.1:5006");args=parser.parse_args()
    root=Path(args.input);destination=root/"tracking_runs.json"
    if destination.exists():raise SystemExit("El registro ya existe; no se duplican las corridas.")
    protocol=json.loads((root/"protocol.json").read_text())
    table=root/"performance.csv";table_hash=hashlib.sha256(table.read_bytes()).hexdigest()
    try:
        exp=json_request(args.url,"/api/2.0/mlflow/experiments/get-by-name?experiment_name=Etapa6_operacion_P1")["experiment"]["experiment_id"]
    except HTTPStatusError as error:
        if error.status!=404:raise
        exp=json_request(args.url,"/api/2.0/mlflow/experiments/create",{"name":"Etapa6_operacion_P1"})["experiment_id"]
    records=[]
    for row in csv.DictReader(table.open(encoding="utf8")):
        stamp=int(time.time()*1000)
        tags={"mlflow.runName":row["run"],"purpose":"registro de resultados observados de carga",
              "source_commit":protocol["source_commit"],"model_bundle_sha256":protocol["model_bundle_sha256"],
              "performance_sha256":table_hash}
        result=json_request(args.url,"/api/2.0/mlflow/runs/create",{"experiment_id":exp,"start_time":stamp,"tags":[{"key":k,"value":v} for k,v in tags.items()]})
        run_id=result["run"]["info"]["run_id"]
        metrics=[{"key":key,"value":float(row[key]),"timestamp":stamp,"step":0} for key in ["requests","failures","successful_predictions","requests_per_second","predictions_per_second","p95_ms","individual_p95_ms","batch10_p95_ms"]]
        params=[{"key":k,"value":row[k]} for k in ["users","repeat","duration_seconds","slo_passed"]]
        json_request(args.url,"/api/2.0/mlflow/runs/log-batch",{"run_id":run_id,"metrics":metrics,"params":params,"tags":[]})
        json_request(args.url,"/api/2.0/mlflow/runs/update",{"run_id":run_id,"status":"FINISHED","end_time":int(time.time()*1000)})
        records.append({"measurement":row["run"],"run_id":run_id})
    destination.write_text(json.dumps({"experiment_id":exp,"tracking_scope":"almacén operativo local; no sustituye el Registry histórico","performance_sha256":table_hash,"runs":records},indent=2,ensure_ascii=False),encoding="utf8")
    print("Métricas registradas en tracking:",len(records))

if __name__=="__main__":main()
