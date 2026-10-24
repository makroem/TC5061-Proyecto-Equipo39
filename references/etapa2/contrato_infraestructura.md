# Infraestructura común de la segunda entrega

Responsable: Marco. Revisión: Stefania. Estas interfaces están implementadas en la rama
de infraestructura. No acreditan aún el entrenamiento de la segunda entrega.

## Punto de partida

`starting_point.json` conserva los seis modelos históricos. Sus identificadores y métricas
se contrastaron con SQLite. Se respaldaron la base oficial y sus 53 archivos de artefactos
fuera de Git. Se mantienen el periodo de doce meses, la partición temporal, los objetivos
y los manifiestos de la entrega anterior. No se usa el antiguo almacén de referencia.

## Entorno y servidor

`python_env.yaml` declara Python 3.11.9 y dependencias de construcción.
`requirements.txt` conserva las versiones de la entrega anterior. `MLproject` referencia
el entorno; Diego Martinez implementará los puntos nuevos `train`, `register` y `verify_registry`.

Antes de instalar, comprobar `python --version`, `python -m pip --version` y
`python -c "import mlflow, sklearn; print(mlflow.__version__, sklearn.__version__)"`.
Si ya son correctos, reutilizar el entorno. Si falta, crear `.venv` con Python 3.11.9,
activar e instalar `python -m pip install -r requirements.txt` y `python -m pip install -e .`.

Desde la carpeta privada que **ya contiene la base oficial**, iniciar en una terminal:

```powershell
python -m mlflow server --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlartifacts --serve-artifacts --host 127.0.0.1 --port 5000
```

Desde el clon y con el entorno activo, en otra terminal:

```powershell
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
$env:MIBICI_RESULTS_DIR = Join-Path $env:LOCALAPPDATA 'MiBiciEquipo39/resultados'
python -m pytest tests -q
```

Interfaz: http://127.0.0.1:5000. Los experimentos existentes conservan su ubicación de
artefactos. Colab necesita un servidor propio; su localhost no apunta al equipo de Marco.
No se fusionan bases SQLite de distintas personas. En Windows usar un `--basetemp` corto
para las pruebas si las rutas temporales exceden el límite del sistema.

## Configuración común

`config.STAGE2_SEARCH_PLAN` fija tres candidatos por pregunta y reutiliza `SEED`:
P1 HGB 100, HGB 200 y Random Forest 300; P2 logística C 0.1, 1 y 10;
P3 KMeans 4, KMeans 5 y GaussianMixture 3. El baseline se conserva por separado.
`REGISTERED_MODELS`, `MODEL_ALIAS`, `REGISTRY_URI` y `RESULTS_DIR` centralizan los
nombres, champion y destinos privados. No se guardan resultados temporales en Git.

## Uso del contrato de artefactos

```python
with tracking.question_run(nombre_descriptivo):
    mlflow.set_tags(tags)
    mlflow.log_params(parametros)
    mlflow.log_metrics(metricas)
    uri = tracking.log_candidate_artifacts(
        modelo_completo, ejemplo_agregado.iloc[:3], configuracion_resuelta,
        flavor="sklearn", plots=rutas_graficas, evaluation=resumen_evaluacion,
    )
```

La función se llama después del entrenamiento dentro de un run activo. No entrena ni
selecciona modelos. Para un `mlflow.pyfunc.PythonModel`, usar `flavor="pyfunc"` y un método
`predict(context, model_input, params=None)`. P1 incluye su codificación de estación; P2 las
dos cabezas, preprocesamiento y umbrales; P3 el escalador.

La firma se infiere de la predicción real. Se registra un ejemplo de una a cinco filas
agregadas, requisitos y código del módulo. Se devuelve `runs:/.../model`.

```text
model/       modelo cargable, firma, ejemplo y entorno
data/        data_manifest.json y split_manifest.json
config/      resolved.json con valores efectivos
plots/       gráficas producidas por cada responsable
evaluation/  summary.json cuando se proporciona
```

El llamador entrega las gráficas pertinentes y la configuración completa. El filtro de
claves sensibles y la validación de versiones detectan errores comunes; cada responsable
revisa además el contenido para excluir datos personales, credenciales y filas de viajes.
`question_run` admite el padre creado por Projects y búsquedas anidadas. La interfaz anterior
`log_model_run` se conserva para reproducir la primera entrega.

Etiquetas obligatorias del llamador: `team`, `question`, `model_family`, `stage_of_work`,
`git_commit`, `git_dirty`, `executor` y `code_author`. Usar `common_tags` y completar las de
búsqueda. La función de artefactos añade `data_version`, `split_id`, `split_version` y
`artifact_contract`. Las métricas llevan prefijos `train_`, `val_` y `test_`.

Las pruebas del contrato usan datos pequeños y un almacén temporal separado. No cuentan
como candidatos oficiales ni asignan champion. Cubren carga en otro proceso, firma,
estructura de artefactos, campos sensibles y versiones inconsistentes.

## Dependencias para continuar

1. Stefania revisa el PR de infraestructura. Marco espera aprobación antes de integrar.
2. Diego Martinez incorpora el controlador, `train` parametrizado, búsquedas anidadas y
   registro, usando este contrato y el entorno declarado.
3. Stefania adapta P1; Diego Martinez adapta P2; Diego Hurtado adapta P3. Cada persona agrega
   empaquetado, métricas, gráficas y pruebas propias mediante PR revisado.
4. Marco revisa el PR de Diego Hurtado cuando exista. Una vez integradas las tres preguntas,
   lanza la ejecución oficial con `mlflow run` y el repositorio limpio.
5. La selección se fija usando validación antes de evaluar test. El equipo revisa
   `selection.json`. Marco verifica carga de cada ganador antes de asignar champion.
6. Marco reproduce desde un clon limpio y captura evidencia. Diego Hurtado integra el reporte.

Los comandos nuevos del manual dependen del controlador y de las adaptaciones pendientes;
no se presentan como puntos de entrada disponibles en esta rama.
