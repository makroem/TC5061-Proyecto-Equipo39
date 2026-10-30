# Actualización parcial de dependencias — Etapa 3

Marco preparó esta actualización el 28 de octubre de 2026 sobre la rama del
[PR #29](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/29).
Su integración requiere revisión independiente y que primero se integre ese PR.

## Versiones propuestas

| Paquete | Versión anterior | Versión comprobada |
|---|---|---|
| certifi | 2026.7.22 | 2026.10.23 |
| requests | 2.32.3 | 2.34.2 |
| pytest | 8.3.5 | 9.0.3 |
| python-dotenv | 1.0.1 | 1.2.2 |

Los cambios están en `requirements.txt`. `requirements-quality.txt` y
`python_env.yaml` lo utilizan como fuente de dependencias. Se mantienen las otras
versiones, incluyendo NumPy, pandas, scikit-learn y MLflow. No se modifican fechas,
particiones, manifiestos, código de los modelos ni selecciones oficiales.

## Resultados comprobados

Se probó el commit `8b63701a158d6ab9191143f3283bcc18fd5a9022` en un entorno nuevo
de Windows con Python 3.11.9:

- Instalación completa y `pip check` sin incompatibilidades.
- 155 pruebas aprobadas, ninguna omitida y 32 avisos; cobertura global de 80.38 %.
- HTTPS del catálogo de MiBici: respuesta 200 con validación del certificado.
- Configuración sintética: lectura correcta y variable existente conservada.
- Bandit sobre el script nuevo: ningún hallazgo.
- Auditoría de los 119 paquetes: cuatro paquetes dejan de reportar avisos.
  Los paquetes con hallazgos pasan de seis a dos; los pares únicos de paquete y
  aviso pasan de 36 a 31. Las entradas reportadas pasan de 68 a 58 porque incluyen
  identificadores repetidos. No se presentan como 58 vulnerabilidades independientes.

Los [resultados y hashes](../../reports/etapa3/actualizacion_dependencias.json)
identifican las versiones y registros examinados. La
[captura del registro exportado](../../reports/figures/etapa3/E12_actualizacion_dependencias.jpg)
resume esta ejecución; no es una captura directa de la consola. Los registros
completos permanecen en `private_quality/dependency_update/`, fuera de Git.
Los resultados anteriores se conservan para comparar, sin sustituir su fecha o alcance.

## Reproducción en un entorno independiente

Desde la raíz del repositorio, verificar primero las instalaciones:

```powershell
Get-Command python, git -ErrorAction SilentlyContinue
python --version
git --version
Test-Path .venv-security/Scripts/python.exe
```

Se requiere Python 3.11.9. Si el entorno existe, comprobar su versión antes de
reutilizarlo. Si falta, crearlo con el intérprete validado; no sustituir los entornos
históricos que conservan las corridas anteriores.

```powershell
python -m venv .venv-security
.venv-security/Scripts/python.exe -m pip install -r requirements-quality.txt
.venv-security/Scripts/python.exe -m pip install --no-deps -e .
.venv-security/Scripts/python.exe -m pip check
```

Crear una carpeta temporal nueva y corta para la suite de Windows:

```powershell
$tempDeps = Join-Path ([System.IO.Path]::GetTempPath()) ('eq39d_' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (Test-Path -LiteralPath $tempDeps) { throw 'Usar un temporal nuevo.' }
New-Item -ItemType Directory -Force private_quality/dependency_update | Out-Null
$env:OMP_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
.venv-security/Scripts/python.exe -m pytest -q --basetemp="$tempDeps" --cov=mibici_equipo39 --cov-report=term-missing --cov-report=json:private_quality/dependency_update/coverage.json --junitxml=private_quality/dependency_update/pytest.xml
.venv-security/Scripts/python.exe scripts/check_dependency_update.py
.venv-security/Scripts/python.exe -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off -f json -o private_quality/dependency_update/pip_audit_after.json
```

Comprobar `$LASTEXITCODE` después de cada comando. La auditoría permanece con salida
1 mientras MLflow y PyArrow tengan avisos; no se debe confundir con una instalación
fallida. El script de compatibilidad consulta por HTTPS el catálogo público configurado,
verifica el certificado con el paquete certifi y lee solo el comienzo de la respuesta.
No guarda el CSV. La comprobación de dotenv usa únicamente valores sintéticos y
confirma que `override=False` conserva una variable existente. No lee archivos `.env`.

## Dependencia que requiere coordinación

Los metadatos de MLflow 2.22.0 exigen `pyarrow<20,>=4.0.0`. El auditor señala
PyArrow 23.0.1 como versión corregida para el aviso encontrado. Actualizarlo de
forma aislada produciría un entorno incompatible. El entorno separado de DeepChecks
ya utiliza PyArrow 23.0.1, pero eso no cambia la restricción del entorno de entrenamiento.

La siguiente migración corresponde a Marco y Diego Martinez, con revisión de los
responsables de P1 y P3. Antes de modificar el servidor oficial, deben comprobar
en un entorno aislado:

1. Resolución de todas las dependencias y auditoría de la versión candidata de MLflow.
2. Puntos de entrada de MLflow Projects y organización de las corridas anidadas.
3. Guardado de modelos, firmas y ejemplos de entrada; rutas de artefactos.
4. Registro, linaje, carga por nombre y alias, sin cambiar los modelos oficiales.
5. Lectura Parquet, conteos, hashes y reproducción de resultados con la misma partición.
6. Respaldo y prueba de restauración del almacenamiento antes de cualquier migración oficial.

Los avisos sin versión corregida requieren análisis de aplicabilidad; no se consideran
resueltos por elegir una versión más reciente. Los cinco avisos bajos de Bandit del
código existente conservan el seguimiento descrito en
[hallazgos.md](../../reports/etapa3/hallazgos.md).

## Fuentes de versiones y restricciones

- Pytest. (2026). [pytest 9.0.3](https://pypi.org/project/pytest/9.0.3/). PyPI.
- Python-dotenv. (2026). [python-dotenv 1.2.2](https://pypi.org/project/python-dotenv/1.2.2/). PyPI.
- Requests. (2026). [requests 2.34.2](https://pypi.org/project/requests/2.34.2/). PyPI.
- Certifi. (2026). [certifi 2026.10.23](https://pypi.org/project/certifi/2026.10.23/). PyPI.
- MLflow. (s. f.). [Metadatos de MLflow 2.22.0](https://pypi.org/pypi/mlflow/2.22.0/json). PyPI.
