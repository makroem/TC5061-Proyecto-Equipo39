# Reproducción de la Etapa 2 sin entrada manual

Revisión del 2 de noviembre de 2026. Implementación y consolidación: Marco. Revisión independiente solicitada: Diego Hurtado. Esta corrección no requiere una aprobación nueva de los responsables históricos de cada pregunta; conserva las selecciones ya integradas.

## Preparación del entorno

Comprobar `git --version` y `python --version`. El proyecto requiere Python 3.11.9. Desde una carpeta de trabajo, clonar el repositorio e instalar las dependencias fijas del mismo commit que se va a ejecutar. En PowerShell:

```powershell
git clone https://github.com/makroem/TC5061-Proyecto-Equipo39.git
cd TC5061-Proyecto-Equipo39
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
$env:Path = (Resolve-Path .venv\Scripts).Path + ';' + $env:Path
python -m pip check
```

Usar el commit revisado que contiene el punto de entrada `reproduce`. La instalación actual fija MLflow 3.17.2 y PyArrow 23.0.1. Las cifras oficiales del reporte pertenecen al entorno histórico indicado en sus corridas. No mezclar los tiempos de ambos entornos.

## Almacén independiente

Para comprobar la reproducción sin escribir en el servidor oficial, usar una base local nueva dentro de una carpeta excluida de Git. No ejecutar este ejemplo apuntando al servidor compartido durante una revisión.

```powershell
New-Item -ItemType Directory -Force private_tracking | Out-Null
$env:MLFLOW_TRACKING_URI = 'sqlite:///private_tracking/reproduccion.db'
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
mlflow run . -e reproduce --env-manager local --experiment-name mibici-equipo39 -P member=Marco -P approved_registry_uri=sqlite:///private_tracking/reproduccion.db
if ($LASTEXITCODE -ne 0) { throw 'La reproducción no terminó; consultar el error antes de continuar.' }
```

El comando comprueba las tres selecciones, ejecuta `ingest`, reproduce P1, P2 y P3 mediante `train`, obtiene la hija seleccionada del padre exacto que acaba de terminar, registra las tres reproducciones y ejecuta `verify_registry`. No pide identificadores, no busca la corrida global más reciente y no necesita que el almacén contenga las corridas históricas.

El resultado queda en `private_results/stage2/workflow_<identificador>.json` y en el artefacto `evaluation/reproduction.json` de la corrida del flujo. La interfaz puede abrirse después con `mlflow ui --backend-store-uri sqlite:///private_tracking/reproduccion.db --port 5002`. Los modelos del almacén nuevo son comprobaciones de reproducción; las capturas oficiales históricas permanecen identificadas por separado.

## Selecciones y control del registro

El flujo bloquea el registro por defecto. El parámetro `approved_registry_uri` debe indicar literalmente el destino autorizado y coincidir con `MLFLOW_REGISTRY_URI`; si esta variable no existe, se utiliza el destino de tracking configurado. La comprobación ocurre antes de conectarse al Registry, ingerir datos o entrenar. MLflow Projects puede crear su corrida contenedora antes del bloqueo; esa corrida fallida no crea versiones ni cambia aliases.

El comando documentado autoriza únicamente `sqlite:///private_tracking/reproduccion.db`. Si el entorno apunta al servidor oficial, el comando se rechaza. Para autorizar deliberadamente otro destino se debe revisar su URI y escribirla explícitamente en el parámetro; no sustituir el valor literal por una variable que acepte inadvertidamente cualquier servidor. Los procesos hijos reciben el destino validado. El parámetro queda registrado en MLflow y no debe contener contraseñas ni tokens.

`references/etapa2/selection.json` ya forma parte del repositorio. Contiene P1 baseline, P2 logística C=0.1 con umbrales 0.65 y 0.70, y P3 GMM de tres componentes. El flujo verifica la versión de datos, la partición, los hiperparámetros y la calibración antes de entrenar. No hay que editar ese archivo para repetir la selección aprobada. Una futura selección distinta debe discutirse y versionarse en otro PR antes de reproducirla.

Si un entrenamiento falla, no se inicia ningún registro. El registro verifica origen, estado, firma y carga antes de asignar cada alias. La asignación de los tres alias es secuencial, no transaccional; un fallo durante registro puede dejar una parte registrada en el almacén autorizado. Por eso la comprobación se hace en un almacén independiente y se revisa `verify_registry` al final. El servidor oficial requiere una autorización explícita de su destino; el comando de comprobación anterior no la concede.

Los puntos de entrada `train`, `registry` y `verify_registry` siguen disponibles para tareas específicas; ya no son pasos manuales necesarios de la reproducción completa.

## Disponibilidad de las fuentes

El 2 de noviembre de 2026 el intento desde un clon sin datos se detuvo porque el catálogo de septiembre devolvió HTTP 404. Se comprobó también el enlace con `www` publicado por el portal, sin obtener el CSV con el cliente de ingesta. No se alteraron los hashes ni se sustituyeron los datos por otro periodo.

La validación adicional utiliza las copias históricas de los trece CSV, verificadas contra el manifiesto. El descargador reutiliza una copia local únicamente si coincide su hash. Esta comprobación permite evaluar el flujo completo, pero no acredita que hoy se puedan descargar todas las fuentes desde una máquina sin esos archivos. El acceso a las fuentes originales sigue siendo un requisito externo. Los CSV y los modelos no se publican en GitHub.

## Resultado de la comprobación del 2 de noviembre

El comando completo terminó en el commit `d3ddd10`, desde una copia limpia del código con las fuentes históricas en caché. Se reconstruyeron 4,497,119 viajes y 4,108,440 filas; P1, P2 y P3 terminaron, se registraron y cargaron por alias en la base independiente. La comparación de 68 métricas y conteos con las búsquedas oficiales coincide con tolerancia relativa 1e-8 y absoluta 1e-10. Los tiempos y tamaños no forman parte de esa comparación.

La corrida del flujo es `1506890ec2ca4b2f9f8c9f853d7565f7` y la verificación final es `397bd04519c3497299c06be2813c2ee1`. Los identificadores detallados y límites constan en [validacion_correcciones_20261102.json](validacion_correcciones_20261102.json).

Pasaron 101 pruebas del flujo, los adaptadores, los artefactos y el registro, con 0 fallos y 21 advertencias, en 579.56 segundos. No se repitió toda la auditoría de seguridad de la tercera etapa. El intento inicial sin caché que devolvió 404 queda documentado y no se presenta como una descarga exitosa.

## Comprobación adicional de la protección del Registry

La protección del destino pasó 22 pruebas del flujo, sin fallos ni omisiones. Se ejecutó también `mlflow run` con la autorización predeterminada ausente y una base SQLite nueva: terminó con el bloqueo previsto, sin modelos, versiones ni aliases registrados. La corrida contenedora quedó como `FAILED`, que es el resultado esperado de este ensayo. Bandit no encontró hallazgos en `reproduce.py`.

Los casos comprueban que una autorización local no permite escribir en el servidor compartido, que los procesos hijos heredan el destino validado y que se conservan los controles de selección y vínculo entre corridas. El detalle está en [validacion_proteccion_registry_20261102.json](validacion_proteccion_registry_20261102.json). Este ensayo complementa las pruebas históricas; no repite el entrenamiento ni modifica el Registry oficial.

## Revisión de Diego Hurtado

Revisar el PR de esta corrección, contrastar las tablas y figuras del reporte con las evidencias oficiales y comprobar los resultados de pruebas y de la reproducción. Confirmar que la limitación de descarga quede visible y que ninguna evidencia de prueba se presente como registro oficial. Marco integra únicamente después de esa aprobación y de resolver los comentarios del PR.
