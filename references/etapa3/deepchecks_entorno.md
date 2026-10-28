# Compatibilidad de DeepChecks

Marco comprobó DeepChecks 0.19.1 el 28 de octubre de 2026 con Python 3.11.9.
El entorno del proyecto conserva NumPy 2.1.3. Aunque el instalador acepta esa
combinación, importar `deepchecks.tabular.checks` falla porque el paquete utiliza
`np.Inf`, retirado en NumPy 2. Por eso DeepChecks se ejecuta en un entorno independiente.

## Entorno comprobado

`requirements-deepchecks.txt` fija las 112 dependencias del entorno separado,
incluyendo NumPy 1.26.4, pandas 2.2.3, scikit-learn 1.6.1, Plotly 5.24.1,
IPython 8.37.0 y PyArrow 23.0.1.
Se comprobó la importación y `pip check`, además de ejecutar y exportar dos casos.
No se cambiaron las versiones de entrenamiento ni se cargaron modelos serializados allí.

Antes de instalar, comprobar si el entorno ya existe:

```powershell
Test-Path .venv-deepchecks/Scripts/python.exe
```

Si existe, verificar primero `.venv-deepchecks/Scripts/python.exe --version` y
`.venv-deepchecks/Scripts/python.exe -m pip show deepchecks numpy`.
Si falta, crearlo con el Python 3.11.9 previamente comprobado:

```powershell
python -m venv .venv-deepchecks
.venv-deepchecks/Scripts/python.exe -m pip install -r requirements-deepchecks.txt
.venv-deepchecks/Scripts/python.exe -m pip check
.venv-deepchecks/Scripts/python.exe scripts/check_deepchecks_env.py
```

En Linux/macOS usar `.venv-deepchecks/bin/python`; esa plataforma no se ha probado aquí.
El script genera `private_quality/deepchecks_smoke/variable.html`, `constant.html`
y `summary.json`. Abrir ambos HTML en el navegador para verificar que se muestran.

## Qué demuestra la comprobación

El caso variable satisface la condición de no tener una sola constante. El caso
constante incumple esa condición. El programa termina correctamente solo si se observan
ambos resultados y las comprobaciones se ejecutaron. Los HTML se exportan sin requerir
conexión para consultar sus resultados. Los hashes quedan en el resumen.

Esto demuestra compatibilidad básica de importación, ejecución, detección negativa
y exportación. No demuestra todavía que todos los checks que elegirá Diego Martinez
sean compatibles ni que los datos reales cumplan los criterios de calidad.

## Entrega a Diego Martinez

Puede reutilizar este entorno para implementar `validation/data_checks.py` y probar
sus comprobaciones con fixtures antes de usar datos reales. Debe confirmar que los
Parquet leídos corresponden a los manifiestos oficiales y mantener las particiones.
Si necesita otro formato, el exportador debe conservar esquema, conteos y hashes.
El contrato de estados y códigos de salida está en [contrato_calidad.md](contrato_calidad.md).

Las dependencias de este entorno también se auditan; compatibilidad funcional no
equivale a ausencia de vulnerabilidades. Consultar el resumen y los hallazgos de seguridad.

La auditoría de las 112 versiones no reportó avisos conocidos el 28 de octubre de 2026.
Un Parquet sintético escrito por el entorno del proyecto se leyó con este entorno,
conservando columnas, dos registros y el hash lógico. El resultado se conserva en
[parquet_interoperabilidad.json](../../reports/etapa3/parquet_interoperabilidad.json).
Esa prueba de transporte no acredita que todos los checks o los datos reales estén validados.
