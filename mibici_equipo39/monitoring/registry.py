"""Fija la versión A por número y comprueba su linaje en el Registry existente."""

import json
import os

from .common import ROOT, load_config, parser, save_json


def tracking(config):
    import mlflow
    uri = os.environ.get("MLFLOW_TRACKING_URI", "")
    if not uri.startswith(("http://", "https://")):
        raise ValueError("Define MLFLOW_TRACKING_URI con el servidor oficial existente.")
    mlflow.set_tracking_uri(uri)
    mlflow.set_registry_uri(uri)
    client = mlflow.MlflowClient()
    if client.get_experiment_by_name(config["experiment"]) is None:
        raise ValueError("El servidor no contiene el experimento histórico del equipo.")
    return client


def freeze(config):
    import mlflow
    client = tracking(config)
    model = client.get_model_version_by_alias(config["model_name"], config["model_alias"])
    if model.version != config["expected_a_version"] or model.run_id != config["expected_a_run"]:
        raise ValueError("El champion cambió; revisar el protocolo antes de continuar.")
    run = client.get_run(model.run_id)
    data_version = run.data.tags.get("data_version", run.data.params.get("data_version"))
    if data_version != config["historical_data_version"]:
        raise ValueError("La versión de datos del modelo A no coincide.")
    uri = f"models:/{config['model_name']}/{model.version}"
    info = mlflow.models.get_model_info(uri)
    if info.signature is None or info.signature.inputs.input_names() != config["features"]:
        raise ValueError("La firma de A es incompatible con el protocolo.")
    path = ROOT / "references/etapa5/models.json"
    existing = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if existing and existing["protocol_sha256"] != config["protocol_sha256"]:
        raise ValueError("El protocolo cambió después de fijar las versiones.")
    existing.update({"protocol_sha256": config["protocol_sha256"], "model_name": model.name,
                     "a": {"version": model.version, "run_id": model.run_id, "uri": uri,
                           "alias_at_freeze": config["model_alias"], "data_version": data_version,
                           "signature": info.signature.to_dict(),
                           "git_commit": run.data.tags.get("git_commit", run.data.tags.get("mlflow.source.git.commit"))},
                     "automatic_promotion": False})
    save_json(path, existing)
    print(json.dumps({"a_version": model.version, "a_run": model.run_id, "signature_columns": len(config["features"])}))


if __name__ == "__main__":
    args = parser(__doc__).parse_args()
    freeze(load_config(args.config))
