# Reproducir la Etapa 5

Usar Python 3.11.9. Antes de instalar, comprobar `python --version` y `python -m pip show mlflow pandas pyarrow`. Conservar el entorno de las etapas anteriores; crear uno nuevo si no existe un entorno compatible.

## 1. Datos históricos y servidor

Seguir la instalación e ingesta histórica del README desde un clon limpio. La carpeta `data` debe contener las particiones verificadas, metadata y objetivos; se puede indicar otra carpeta local ya verificada con `--historical-data`. Este parámetro no cambia el manifiesto histórico.

Iniciar el almacén oficial existente con el procedimiento de `scripts/start_tracking.ps1`. No usar una base vacía para sustituir el Registry. En PowerShell:

```powershell
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
python -m mibici_equipo39.monitoring.registry
python -m mibici_equipo39.monitoring.prepare --historical-data data
python -m pytest tests/monitoring -q
```

La preparación verifica las huellas de las 12 mensualidades históricas y descarga octubre de 2026 y su catálogo. Se detiene si cambia un CSV cuya huella ya quedó registrada. No se deben subir los CSV ni los Parquet a Git.

## 2. Evidently en un entorno separado

Comprobar si existe `.venv-monitor` y ejecutar su Python con `-m pip show evidently`. Si no existe, crearlo e instalar las versiones fijadas:

```powershell
python -m venv .venv-monitor
.\.venv-monitor\Scripts\python.exe -m pip install -r requirements-monitoring.txt
$env:DO_NOT_TRACK = '1'
.\.venv-monitor\Scripts\python.exe -m mibici_equipo39.monitoring.drift
```

Evidently solo lee los Parquet y escribe reportes. El entrenamiento y el Registry siguen usando el entorno histórico con scikit-learn 1.6.1; no instalar las dependencias de Evidently encima de ese entorno.

## 3. B y comparación

Confirmar el código y el protocolo en Git antes de entrenar; se rechaza un árbol de trabajo con cambios sin confirmar para conservar el vínculo entre run y commit. Ejecutar con el Python del entorno histórico:

```powershell
python -m mibici_equipo39.monitoring.train_b
python -m mibici_equipo39.monitoring.ab_test
```

Si B ya está registrada según `models.json`, se verifica la versión existente y no se duplica el entrenamiento. En un Registry independiente no se deben reutilizar números de versión de otro almacén: revisar primero su linaje con Diego Hurtado. Las versiones de A/B del manifiesto identifican el almacén oficial de esta entrega.

Los resultados se guardan en `reports/etapa5/`; las predicciones por fila en `private_results/etapa5/` permanecen excluidas de Git. Ninguno de estos comandos cambia el alias `champion`.

## 4. Revisión y evidencia pendiente

Diego Hurtado revisa el PR técnico, las huellas, las fechas y la comparación. Después se toman capturas auténticas del HTML de Evidently, de la ficha A/B y de los resultados. Las capturas deben mostrar la versión y los datos vigentes. El reporte final debe distinguir observaciones, límites y recomendaciones; no declarar una mejora antes de consultar los resultados.
