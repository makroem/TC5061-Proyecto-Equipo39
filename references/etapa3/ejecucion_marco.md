# Ejecución de las verificaciones de Marco

Ejecutar desde la raíz del repositorio. Estos pasos comprueban la infraestructura
disponible; la validación final de datos reales depende del motor de Diego Martinez
y de los criterios revisados de P1, P2 y P3.

## 1. Comprobar las instalaciones

En PowerShell:

```powershell
Get-Command git, python, py -ErrorAction SilentlyContinue
Test-Path .venv-a7/Scripts/python.exe
```

Si existe el entorno, comprobar su versión con `.venv-a7/Scripts/python.exe --version`.
Si no existe, comprobar que el intérprete elegido sea Python 3.11.9 antes de crearlo.
Se puede usar la ruta de una instalación disponible. Solo si falta Python, instalarlo
desde [Python 3.11.9](https://www.python.org/downloads/release/python-3119/).
Comprobar Git con `git --version`; si falta, usar [Git para Windows](https://git-scm.com/downloads/win).

```powershell
python --version
python -m venv .venv-a7
.venv-a7/Scripts/python.exe -m pip install -r requirements-quality.txt
.venv-a7/Scripts/python.exe -m pip install --no-deps -e .
.venv-a7/Scripts/python.exe -m pip check
```

No es necesario activar el entorno ni cambiar la política de ejecución de PowerShell.
En Linux/macOS sustituir `.venv-a7/Scripts/python.exe` por `.venv-a7/bin/python`.
La comprobación realizada para esta entrega corresponde a Windows y Python 3.11.9.

## 2. Ejecutar pruebas

Usar una carpeta temporal nueva y una ruta corta. Esto evita conflictos de permisos
y el límite de longitud de rutas de Windows al guardar artefactos de MLflow.

```powershell
$runA7 = Get-Date -Format 'yyyyMMdd_HHmmss'
$tempA7 = Join-Path ([System.IO.Path]::GetTempPath()) ('eq39_' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (Test-Path -LiteralPath $tempA7) { throw 'Usar un temporal nuevo.' }
$env:OMP_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
New-Item -ItemType Directory -Force private_quality | Out-Null
.venv-a7/Scripts/python.exe -m pytest --collect-only -q
.venv-a7/Scripts/python.exe -m pytest -m 'not integration and not data_quality' -q --basetemp="$tempA7-rapidas"
.venv-a7/Scripts/python.exe -m pytest tests/test_ingesta_calidad.py tests/test_data.py tests/test_download.py tests/test_runtime_regressions.py -q --basetemp="$tempA7-ingesta" --cov=mibici_equipo39.dataset --cov-report=term-missing --cov-report=json:private_quality/coverage_ingesta.json
.venv-a7/Scripts/python.exe -m pytest -q --basetemp="$tempA7-completa" --cov=mibici_equipo39 --cov-report=term-missing --cov-report=json:private_quality/coverage_total.json --junitxml=private_quality/pytest.xml
```

Comprobar `$LASTEXITCODE` después de cada ejecución. Una salida 0 confirma que las
pruebas seleccionadas pasaron. Una suite sintética aprobada no acredita la ausencia
de problemas en los CSV reales. No se descargan datos ni se reentrenan modelos oficiales.

## 3. Análisis estático y dependencias

```powershell
.venv-a7/Scripts/python.exe -m bandit --version
.venv-a7/Scripts/python.exe -m pip_audit --version
.venv-a7/Scripts/python.exe -m bandit -r mibici_equipo39 -f json -o private_quality/bandit.json
.venv-a7/Scripts/python.exe -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off -f json -o private_quality/pip_audit.json
.venv-a7/Scripts/python.exe -m pip_audit -r requirements-quality.txt --no-deps --disable-pip --progress-spinner off -f json -o private_quality/pip_audit_quality.json
```

El análisis consulta las versiones fijadas. `--no-deps --disable-pip` evita resolver
un entorno distinto durante la auditoría; por eso las dependencias transitivas están
enumeradas en los archivos de requisitos. Una salida 1 con hallazgos no equivale a
un fallo de instalación ni debe ocultarse. Revisar el JSON, versiones e identificadores.
No usar `--fix` en el entorno histórico sin una migración probada y revisada.

## 4. Exclusiones e historial

```powershell
git check-ignore -v .venv-a7/pyvenv.cfg .venv-deepchecks/pyvenv.cfg private_quality/result.json .env mlflow.db mlflow.db-wal mlruns/test mlartifacts/test models/model.joblib data/raw/example.csv
git ls-files
Get-Command gitleaks -ErrorAction SilentlyContinue
```

Si Gitleaks existe, verificar `gitleaks version`. Si falta, obtener la versión
8.30.1 desde su [publicación oficial](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1)
y verificar el SHA256 del archivo contra el publicado. No es necesario instalarlo globalmente.

```powershell
gitleaks git --log-opts='--all' --redact=100 --report-format json --report-path private_quality/gitleaks_history.json .
git archive --format=zip --output=private_quality/tracked.zip HEAD
Expand-Archive -LiteralPath private_quality/tracked.zip -DestinationPath "private_quality/tracked_$runA7"
gitleaks dir --redact=100 --report-format json --report-path private_quality/gitleaks_tracked.json "private_quality/tracked_$runA7"
```

El segundo escaneo cubre los archivos del commit, sin mezclar dependencias instaladas
o datos locales. Guardar los cambios en un commit local antes de escanear este snapshot; en caso contrario
los archivos sin commit no estarán incluidos. El historial abarca las referencias
disponibles en el clon; no incluye commits inaccesibles del servidor.

Con esta versión del auditor y `--disable-pip`, el archivo de calidad reportó solo sus
19 requisitos adicionales. Por eso son obligatorias ambas auditorías: `requirements.txt`
para los 119 paquetes del proyecto y `requirements-quality.txt` para los adicionales.
No interpretar un resultado limpio de los adicionales como aprobación del entorno completo.

## 5. Evidencia y revisión

Guardar versiones, comandos, salida, fecha, commit probado y alcance. Conservar
los registros completos en `private_quality/`; publicar únicamente los resúmenes
y capturas revisados. Las capturas de registros deben identificarse como tales.
Los avisos y comprobaciones pendientes permanecen visibles.

El primer PR de Marco requiere revisión de Stefania. El cierre integrado espera
los PR técnicos del equipo. Los modelos registrados y los manifiestos oficiales
no se modifican para obtener resultados favorables en las pruebas.

## Fuentes de consulta

- pytest. (s. f.). [Documentación](https://docs.pytest.org/en/stable/).
- Python Packaging Authority. (s. f.). [pip-audit](https://pypi.org/project/pip-audit/).
- Python Code Quality Authority. (s. f.). [Bandit: Getting started](https://bandit.readthedocs.io/en/latest/start.html).
- Gitleaks. (2026). [Gitleaks v8.30.1](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
- Deepchecks. (s. f.). [Installation](https://docs.deepchecks.com/stable/getting-started/installation.html).
