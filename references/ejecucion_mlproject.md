# Cómo ejecutar el proyecto

Las dos formas usan `.venv` con `requirements.txt` y Python 3.11.9. `--env-manager local` no crea otro entorno: usa el `python` que esté primero en el PATH.

## Directo

```bash
python -m mibici_equipo39.dataset --verify-manifest
python -m mibici_equipo39.features
python -m mibici_equipo39.modeling.p1 --executor persona3
python -m mibici_equipo39.modeling.p2 --executor persona3
```

## MLflow Projects

Mac o Linux:

```bash
export PATH="$PWD/.venv/bin:$PATH"
export MLFLOW_TRACKING_URI="sqlite:///mlflow.db"
mlflow run . -e features --env-manager local --experiment-name mibici-equipo39
mlflow run . -e main --env-manager local --experiment-name mibici-equipo39 --run-name main-persona3 -P member=persona3
```

Windows (PowerShell):

```powershell
$env:Path = "$PWD\.venv\Scripts;$env:Path"
$env:MLFLOW_TRACKING_URI = "sqlite:///mlflow.db"
mlflow run . -e main --env-manager local --experiment-name mibici-equipo39 --run-name main-persona3 -P member=persona3
```

Cada integrante cambia `member` y `--run-name`. Los runs de modelos quedan anidados bajo el run del proyecto y se filtran con la etiqueta `question`. `main` corre P1 y P2 hasta que el controlador común integre P3.

## Ver resultados

```bash
python -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```
