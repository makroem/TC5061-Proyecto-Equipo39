# Entorno de DeepChecks

DeepChecks 0.19.1 se ejecuta en un entorno separado con Python 3.11.9 y NumPy
1.26.4. El entorno de entrenamiento conserva NumPy 2.1.3. No se mezclan los dos
archivos de requisitos ni se cambian los modelos oficiales para validar datos.

## Comprobar antes de instalar

Desde la raíz del repositorio, en PowerShell:

```powershell
python --version
Test-Path .venv-deepchecks/Scripts/python.exe
```

Si ya existe, consultar primero su versión y los paquetes instalados:

```powershell
.venv-deepchecks/Scripts/python.exe --version
.venv-deepchecks/Scripts/python.exe -m pip show deepchecks setuptools numpy
```

Crear el entorno únicamente si falta y usar Python 3.11.9:

```powershell
python -m venv .venv-deepchecks
```

Instalar las versiones fijadas y preparar la compatibilidad:

```powershell
.venv-deepchecks/Scripts/python.exe -m pip install -r requirements-deepchecks.txt
.venv-deepchecks/Scripts/python.exe scripts/prepare_deepchecks.py
.venv-deepchecks/Scripts/python.exe -m pip check
.venv-deepchecks/Scripts/python.exe scripts/check_deepchecks_env.py
```

Comprobar `$LASTEXITCODE` después de cada comando; detenerse si no es cero.
En Linux/macOS se sustituye `Scripts/python.exe` por `bin/python`; la verificación
de esta actualización corresponde a Windows x86-64.

## Por qué se prepara el paquete

La versión publicada de DeepChecks importa `pkg_resources` en dos utilidades de
presentación. Ese módulo ya no está disponible en setuptools 84.1.0. Mantener
setuptools 81.0.0 conservaba dos avisos de seguridad documentados en el cierre
anterior. La solución actual fija 84.1.0 y aplica una adaptación explícita:

- `utils/display.py` consulta los paquetes mediante `importlib.metadata` y normaliza sus nombres con `packaging.utils.canonicalize_name`.
- `core/serialization/dataframe/html.py` compara versiones con `packaging.version.parse`.

El script comprueba la versión 0.19.1 y los hashes SHA256 de ambos archivos antes
de escribir. Si detecta otro contenido, termina con error. Puede ejecutarse otra
vez sin volver a modificar los archivos. Conserva los avisos de licencia de
DeepChecks e incorpora una nota de modificación local. No cambia checks,
condiciones, métricas, muestras ni umbrales. No modifica el código del entrenamiento.

Después de reinstalar DeepChecks con `--force-reinstall`, repetir la preparación.
Para una versión nueva de DeepChecks se debe revisar esta adaptación; el script
no aplica cambios automáticamente a versiones diferentes. Los hashes originales
y adaptados quedan en su salida JSON. El entorno es una instalación de la versión
oficial con dos archivos adaptados localmente, no una publicación nueva del proveedor.

## Verificación y evidencia

El control sintético ejecuta un caso variable que debe aprobarse y uno constante
que debe incumplir la condición; exporta ambos HTML a
`private_quality/deepchecks_smoke/`. Esto comprueba importación, detección negativa
y exportación, pero no sustituye la validación de datos reales.

```powershell
.venv-a7/Scripts/python.exe -m pytest tests/test_deepchecks_preparation.py tests/test_data_checks.py -q
.venv-a7/Scripts/python.exe -m pip_audit -r requirements-deepchecks.txt --no-deps --disable-pip --progress-spinner off
```

Las pruebas del motor usan datos sintéticos y comprueban también errores y
condiciones fallidas. Los resultados de la actualización se conservan en
[el cierre adicional](../../reports/etapa3/cierre_adicional_marco.md). La evaluación
real del 1 de noviembre mantiene sus resultados originales y su política congelada.

## Fuentes

- [DeepChecks 0.19.1 en PyPI](https://pypi.org/project/deepchecks/0.19.1/).
- [Código y licencia de DeepChecks](https://github.com/deepchecks/deepchecks).
- [Setuptools 84.1.0](https://github.com/pypa/setuptools/releases/tag/v84.1.0).
- [Aviso de seguridad de setuptools](https://github.com/pypa/setuptools/security/advisories/GHSA-xmj3-9gf7-h52w).
- [importlib.metadata](https://docs.python.org/3.11/library/importlib.metadata.html).
- [Versiones en packaging](https://packaging.pypa.io/en/stable/version.html).
