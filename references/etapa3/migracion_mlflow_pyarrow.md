# Migración conjunta de MLflow y PyArrow

Responsable técnico: Marco. La integración requiere la revisión de otro integrante.

## Alcance

El entorno propuesto utiliza Python 3.11.9, MLflow 3.17.2 y PyArrow 23.0.1. También actualiza Tornado a 6.6 por los avisos detectados durante la auditoría. Las versiones completas están fijadas en `requirements.txt`; `requirements.in` expresa las dependencias directas. Se mantienen pandas, NumPy, scikit-learn, las fechas, la partición cronológica, la semilla, las selecciones y los umbrales de la entrega anterior.

La verificación se hace sobre copias. El servidor oficial de la etapa anterior conserva su base y sus artefactos. El cambio de servidor se realiza después de la revisión del PR y de acordar una pausa de escrituras. Este trabajo no sustituye la validación real de DeepChecks ni las contribuciones individuales pendientes de la Actividad 7.

MLflow 3 registra los modelos como objetos propios. Las nuevas corridas guardan `model_uri`, `model_id` y `artifact_contract=3`; el registro utiliza esa URI. Las corridas antiguas conservan la ruta `runs:/ID/model`. Los modelos nuevos se consultan también en la sección de modelos de MLflow, no necesariamente dentro de los artefactos de la corrida.

El formato de los modelos scikit-learn se fija en `cloudpickle`: el baseline de P1 contiene objetos pandas que no admite el nuevo formato predeterminado. Solo se cargan modelos propios con origen y hashes comprobados. Un archivo pickle/cloudpickle de origen desconocido no se considera seguro.

## Resultados comprobados el 28 de octubre de 2026

| Verificación | Resultado |
|---|---|
| Suite de esta rama | 161 pruebas aprobadas, 0 fallos, 0 omisiones y 23 advertencias de las bibliotecas. No incluye el PR #31 pendiente. |
| Dependencias del proyecto | 132 paquetes fijados consultados; 0 avisos conocidos en esa consulta. `pip check` sin conflictos. |
| Migración de la copia SQLite | Integridad correcta; 34 corridas, 500 archivos de artefactos y tres modelos conservados. |
| Recuperación con el entorno anterior | MLflow 2.22.0/PyArrow 19.0.1 cargan los tres alias desde el respaldo restaurado. |
| Parquet | Cinco tablas verificadas entre versiones, en escritura/relectura y después de reconstruirlas desde las fuentes. |
| Ingesta real mediante Projects | 12 meses, 4,497,119 viajes y 4,108,440 filas de características; manifiestos confirmados. |
| Reproducción y registro nuevos | P1, P2 y P3 terminan mediante Projects, conservan las métricas y cargan por `champion` en el almacén de prueba. |

La comparación incluye 68 métricas y conteos: seis de P1, 45 de P2 y 17 de P3. Se excluyeron tiempos y tamaños serializados, que dependen del entorno. La tolerancia de la comprobación numérica fue relativa `1e-10` y absoluta `1e-12`.

| Pregunta y selección | Métrica | Validación anterior / nueva | Prueba anterior / nueva |
|---|---|---|---|
| P1: baseline estacional | MAE | 0.888775 / 0.888775 | 0.916381 / 0.916381 |
| P2: logística C=0.1 | F1 macro | 0.042360 / 0.042360 | 0.052181 / 0.052181 |
| P3: GMM de tres componentes | Silhouette | 0.026594 / 0.026594 | 0.051373 / 0.051373 |

Estos resultados acreditan compatibilidad; no son una mejora predictiva ni una nueva elección de modelos. Los valores completos, identificadores y límites del ensayo están en el [resumen verificable](../../reports/etapa3/migracion_mlflow_pyarrow.json).

## 1. Comprobar el entorno antes de instalar

Abrir PowerShell en la raíz del repositorio y comprobar las instalaciones:

```powershell
Get-Command git, py, python -ErrorAction SilentlyContinue
py -0p
git status --short
```

Usar Python 3.11.9. Si no está instalado, obtenerlo de https://www.python.org/downloads/release/python-3119/. No reemplazar el entorno del servidor anterior. Comprobar primero si existe el nuevo entorno:

```powershell
Test-Path .venv-mlflow3/Scripts/python.exe
```

Solo si devuelve `False`:

```powershell
py -3.11 -m venv .venv-mlflow3
```

Instalar y validar desde el entorno nuevo:

```powershell
& .venv-mlflow3/Scripts/python.exe --version
& .venv-mlflow3/Scripts/python.exe -m pip install -r requirements-quality.txt
& .venv-mlflow3/Scripts/python.exe -m pip install --no-deps -e .
& .venv-mlflow3/Scripts/python.exe -m pip check
& .venv-mlflow3/Scripts/python.exe -c "import mlflow,pyarrow; print(mlflow.__version__, pyarrow.__version__)"
```

Continuar únicamente si la versión de Python y las dos bibliotecas coinciden con las indicadas. El ensayo documentado se realizó en Windows; otro sistema operativo requiere su propia instalación y prueba.

## 2. Preparar un respaldo y una copia independiente

Acordar que nadie ejecute corridas ni modifique el registro durante el respaldo final. Detener el servidor anterior desde su propia terminal cuando llegue el momento del cambio. Conservar su entorno Python para poder volver a utilizarlo.

Definir rutas locales reales. El origen debe contener `mlflow.db` y las carpetas de artefactos. El destino debe ser nuevo, estar fuera del origen y fuera del repositorio. Los siguientes valores son ejemplos que deben sustituirse:

```powershell
$origen = 'C:/MiBici/almacen_actual'
$ensayo = 'C:/MiBici/migracion_nueva'
& .venv-mlflow3/Scripts/python.exe scripts/prepare_tracking_migration.py --source $origen --destination $ensayo
```

El procedimiento abre la base de origen en modo lectura, crea un respaldo SQLite consistente, copia los artefactos, verifica hashes y prepara `candidate/` con rutas independientes. No acepta un destino existente ni rutas solapadas. Si detecta cambios concurrentes, se detiene: repetir en otra carpeta cuando hayan terminado todas las escrituras. No asumir que un respaldo de la base por sí solo incluye los modelos.

Conservar `backup/`, `private_origin.json` y `prepare_summary.json` fuera de Git. El procedimiento cubre este almacén local SQLite y sus carpetas `mlruns/` y `mlartifacts/`. No es un migrador general de servidores remotos ni de artefactos externos.

## 3. Actualizar exclusivamente la copia

```powershell
$dbCandidata = (Join-Path $ensayo 'candidate/mlflow.db').Replace('\', '/')
& .venv-mlflow3/Scripts/python.exe -m mlflow db upgrade "sqlite:///$dbCandidata"
& .venv-mlflow3/Scripts/python.exe scripts/verify_tracking_copy.py --root $ensayo --store candidate
```

La comprobación compara el contenido histórico de corridas, parámetros, métricas, etiquetas, versiones y alias; verifica los hashes de los artefactos y carga los tres `champion`. Las predicciones deben coincidir con los ejemplos registrados. El script también comprueba que la base original no haya cambiado durante el ensayo. Una migración de esquema no se revierte instalando una versión anterior.

Iniciar la copia en un puerto diferente, desde una terminal dedicada:

```powershell
./scripts/start_tracking.ps1 -StorePath (Join-Path $ensayo 'candidate') -PythonExecutable (Resolve-Path .venv-mlflow3/Scripts/python.exe).Path -Port 5001
```

El lanzador comprueba versiones y esquema antes de iniciar el servidor. Rechaza una base antigua para evitar actualizarla al arrancar. Escucha únicamente en `127.0.0.1`.

En Windows el servidor informa que su servicio de trabajos no está disponible. La ejecución de este proyecto utiliza MLflow Projects local; no requiere ni acredita ese servicio adicional.

Abrir http://127.0.0.1:5001. Capturar la lista de corridas históricas y el registro con los tres modelos y sus alias. Verificar las firmas, ejemplos y el linaje. Las capturas deben identificar el entorno de ensayo y no mostrar rutas personales ni credenciales.

## 4. Verificar los datos y ejecutar el proyecto

Con el entorno anterior, ejecutar `scripts/check_parquet_compatibility.py` sobre los Parquet procesados para guardar una referencia. Con el entorno nuevo, leer esos mismos archivos, compararlos y escribir una copia nueva:

```powershell
$datos = 'C:/MiBici/datos/processed'
$salida = 'C:/MiBici/prueba_parquet'
& .venv-mlflow3/Scripts/python.exe scripts/check_parquet_compatibility.py --input $datos --output "$salida/nuevo.json" --compare "$salida/anterior.json" --roundtrip "$salida/parquet23"
```

`anterior.json` se genera con el mismo script y `--input`/`--output` en el entorno anterior, sin `--compare` ni `--roundtrip`. Leer después `parquet23/` con el entorno anterior y compararlo con `anterior.json`. Se comprueban filas, columnas, tipos, nulos y huellas de valores; la escritura no tiene que producir archivos binariamente idénticos.

Para reproducir entrenamiento, utilizar otro almacén de prueba, independiente del histórico migrado. Configurar ambas URI, activar el entorno y conservar el repositorio limpio:

```powershell
./.venv-mlflow3/Scripts/Activate.ps1
$env:MLFLOW_TRACKING_URI = 'sqlite:///private_tracking/migracion/mlflow.db'
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
$env:MIBICI_RESULTS_DIR = 'private_results/migracion'
New-Item -ItemType Directory -Force private_tracking/migracion | Out-Null
mlflow run . -e ingest --env-manager local --experiment-name mibici-equipo39
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p1 -P model=selected -P member=Marco -P mode=reproduce
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p2 -P model=selected -P member=Marco -P mode=reproduce
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p3 -P model=selected -P member=Marco -P mode=reproduce
```

Comparar las métricas con las corridas oficiales que figuran en `references/etapa2/selection.json`. Los tiempos de ejecución y tamaños de archivos no tienen que coincidir. Comprobar el registro de los nuevos modelos por URI, su firma y sus predicciones antes de asignar `champion` en el almacén de prueba. No registrar ensayos en el servidor oficial.

Ejecutar las pruebas y la auditoría:

```powershell
python -m pytest -q
python -m pip_audit -r requirements.txt
```

Guardar las salidas completas en `private_quality/`. Publicar solo un resumen revisado sin datos de viajes, bases, modelos ni rutas personales. Una auditoría sin avisos conocidos no acredita ausencia de toda vulnerabilidad.

## 5. Ensayar la restauración

```powershell
& .venv-mlflow3/Scripts/python.exe scripts/prepare_tracking_migration.py --restore $ensayo
```

Se crea `restored/` desde el respaldo intacto y se ajustan únicamente sus rutas. Ejecutar `scripts/verify_tracking_copy.py --root $ensayo --store restored` con el Python del entorno anterior. Debe conservar el esquema antiguo, los 34 runs del respaldo de este ensayo, sus artefactos y los tres alias. No ejecutar MLflow 2 contra la base actualizada a MLflow 3.

## 6. Integración y cambio de servidor

Marco prepara el código, las comprobaciones y el PR. Otro integrante revisa los cambios, la evidencia y el procedimiento de restauración. Tras integrar el PR, coordinar la pausa de escrituras, generar un respaldo final nuevo y repetir actualización y verificación. Solo entonces iniciar el nuevo servidor y cambiar las URI de los clientes. Conservar el almacén anterior sin modificaciones y el respaldo durante la aceptación.

Si falla la aceptación, detener el servidor nuevo y volver al almacén anterior con su entorno anterior, o utilizar la copia `restored/` ya verificada. No copiar una base migrada sobre el respaldo. Si existen corridas posteriores al cambio, conservarlas aparte y reconciliarlas antes de volver a admitir escrituras. No mezclar bases SQLite ni sobrescribir modelos.

Las pruebas del ensayo y sus límites se registran en `reports/etapa3/migracion_mlflow_pyarrow.json`. La validación de una copia no afirma que el servidor oficial ya haya cambiado de versión.

Las [capturas del registro y de las corridas](../../reports/etapa3/evidence/migracion/README.md) identifican expresamente el almacén de ensayo.

## Referencias

- MLflow. (s. f.). *Migrating to MLflow 3*. https://mlflow.org/docs/latest/ml/mlflow-3/
- MLflow. (s. f.). *Migration*. https://mlflow.org/docs/latest/self-hosting/migration/
- Python Software Foundation. (s. f.). *MLflow: package metadata*. https://pypi.org/project/mlflow/3.17.2/
- Apache Arrow. (s. f.). *PyArrow*. https://pypi.org/project/pyarrow/23.0.1/
