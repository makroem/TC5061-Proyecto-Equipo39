"""Comprobación HTTP del contrato, identidad del modelo y respuesta de error."""
import argparse
import json
from pathlib import Path
from .http_client import HTTPStatusError, json_request
from .payload import make_payload, valid_response

def require(condition,message):
    if not condition:raise RuntimeError(message)

def check(url,manifest_path):
    manifest=json.loads(Path(manifest_path).read_text(encoding="utf8"))
    require(json_request(url,"/health")["status"]=="ok","Salud inválida")
    ready=json_request(url,"/ready")
    require(ready["model_bundle_sha256"]==manifest["bundle_sha256"],"Huella de modelo distinta")
    require(ready["model_name"]==manifest["model_name"],"Nombre de modelo distinto")
    require(ready["model_version"]==str(manifest["model_version"]),"Versión distinta")
    for size in (1,10,100):
        body=json_request(url,"/predict",make_payload(size,39))
        require(valid_response(body,size),"Contrato de respuesta inválido")
        require(body["model_bundle_sha256"]==manifest["bundle_sha256"],"Huella de predicción distinta")
    try:
        json_request(url,"/predict",{"instances":[]})
    except HTTPStatusError as error:
        require(error.status==422,"Código de rechazo distinto de 422")
    else:
        raise RuntimeError("Una solicitud vacía debe rechazarse.")
    return {"status":"passed","model_name":ready["model_name"],"model_version":ready["model_version"],
            "model_bundle_sha256":ready["model_bundle_sha256"],"valid_batches":[1,10,100],"invalid_status":422}

if __name__=="__main__":
    parser=argparse.ArgumentParser();parser.add_argument("--url",default="http://127.0.0.1:8006")
    parser.add_argument("--manifest",default="references/etapa4/model_manifest.json");parser.add_argument("--output")
    args=parser.parse_args();result=check(args.url,args.manifest)
    if args.output:
        Path(args.output).parent.mkdir(parents=True,exist_ok=True)
        Path(args.output).write_text(json.dumps(result,indent=2),encoding="utf8")
    print(json.dumps(result))
