# Verificación integrada de pruebas y seguridad

Marco ejecutó esta comprobación el **7 de noviembre de 2026**, después de integrar
los PR [#57](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/57)
y [#56](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/56).
El código probado corresponde a `e4ac4c6037d7150ac9b5ea1ba4812030b9e05d99`, con el
árbol de archivos versionados limpio al inicio. El resultado para actualizar el
README se encuentra en [estado_vigente.json](estado_vigente.json).

## Resultado y alcance

| Comprobación | Resultado vigente |
|---|---|
| PyTest, `tests` con `tests/api` excluido | **284 recopiladas y aprobadas; 0 fallos, 0 errores, 0 omisiones** |
| Advertencias de PyTest | **23**, conservadas en el registro |
| DeepChecks integrado en PyTest | 2 casos sintéticos ejecutados y aprobados; incluidos en las 284 pruebas |
| Compatibilidad de DeepChecks, ejecución separada | Ejemplo variable aprobado; ejemplo constante rechazado como se esperaba |
| Bandit, módulo completo | **9 LOW, 0 MEDIUM, 0 HIGH, 0 errores de análisis** |
| Entorno de calidad | Python 3.11.9; 154 requisitos aplicables coincidentes; `pip check` correcto |
| Entorno independiente de DeepChecks | Python 3.11.9; 122 requisitos aplicables coincidentes; `pip check` correcto |

La suite incluye las regresiones compartidas de ingesta, funciones, entrenamiento,
trazabilidad, registro y calidad. Utiliza datos sintéticos y almacenes temporales
aislados. Las **76 pruebas históricas de API no se suman** a este total. Tampoco se
suman las 33 pruebas de la revisión previa del PR #56: esos casos forman parte de
la ejecución completa. El [desglose por módulo](registros_20261107/pytest_por_modulo.json)
permite comprobar la suma de 284.

Los entornos se crearon en un clon nuevo el 5 de noviembre y se reutilizaron tras
volver a comprobar sus versiones. La ejecución actual duró 315.47 segundos según
la consola; el atributo de duración del JUnit registra 315.42 segundos. Se conservan
ambas mediciones, sin presentarlas como corridas diferentes.

## Reproducir desde la raíz

Antes de instalar, comprobar si existen `.venv-a7` y `.venv-deepchecks` y verificar
Python 3.11.9. La [guía de preparación](../../references/etapa3/ejecucion_marco.md)
y la [adaptación de DeepChecks](../../references/etapa3/deepchecks_entorno.md)
describen los dos entornos. Para esta comprobación, usar el alcance siguiente en
lugar de sumar las pruebas de API al entorno de calidad.

En PowerShell, con ambos entornos preparados:

```powershell
$pythonCalidad = '.\.venv-a7\Scripts\python.exe'
$pythonDatos = '.\.venv-deepchecks\Scripts\python.exe'
& $pythonCalidad --version
& $pythonDatos --version
& $pythonCalidad -m pip check
& $pythonDatos -m pip check
$env:OMP_NUM_THREADS = '4'
$env:OPENBLAS_NUM_THREADS = '4'
$env:MKL_NUM_THREADS = '4'
$tempA7 = Join-Path ([IO.Path]::GetTempPath()) ('eq39_' + [guid]::NewGuid().ToString('N').Substring(0,8))
if (Test-Path -LiteralPath $tempA7) { throw 'Usar un temporal nuevo.' }
New-Item -ItemType Directory -Force private_quality/cierre_20261107 | Out-Null
& $pythonCalidad -m pytest tests --ignore=tests/api -q --basetemp="$tempA7" --junitxml=private_quality/cierre_20261107/pytest.xml
& $pythonDatos scripts/check_deepchecks_env.py --output private_quality/cierre_20261107/deepchecks_smoke
& $pythonCalidad -m bandit -r mibici_equipo39 -f json -o private_quality/cierre_20261107/bandit.json
```

Comprobar `$LASTEXITCODE` después de cada orden. PyTest y el control de compatibilidad
terminaron con **0**. Bandit terminó con **1** porque conserva avisos; su lista
`errors` está vacía. En macOS/Linux se utilizan los intérpretes `bin/python` de los
entornos y una carpeta temporal nueva. La ejecución documentada aquí fue en Windows.

## Advertencias y seguridad

Las 23 advertencias de PyTest corresponden a deprecaciones de PyParsing/Matplotlib
y Click/Typer (16), al comportamiento futuro de concatenación de pandas (2) y a
recomendaciones de MLflow sobre tipos y valores ausentes en firmas (5). No son
fallos de prueba ni se cuentan como hallazgos de Bandit. Se conservan completas en
el [registro de PyTest](registros_20261107/pytest.txt). Una futura actualización de
estas bibliotecas requiere repetir la regresión; esta comprobación no cambió las
versiones ni silenció las advertencias.

El [JSON de Bandit](registros_20261107/bandit.json) conserva el contenido original
con saltos de línea normalizados para Git. Las huellas del archivo local y del
publicado se registran por separado. Hay nueve avisos, todos LOW y de confianza HIGH:

| Ubicación | Regla | Interpretación y control |
|---|---|---|
| `modeling/p1.py:12` | B403 | Importa `pickle` para medir el tamaño con `dumps`; no carga una entrada externa en esta operación. Mantener la carga de modelos limitada a artefactos confiables. |
| `modeling/p3.py:11` | B403 | Mismo uso de medición de tamaño; conserva la misma restricción de procedencia. |
| `modeling/tracking.py:6` | B404 | Importación de procesos para comprobar Git. Las llamadas internas usan listas fijas y no reciben órdenes de una solicitud. |
| `modeling/tracking.py:18` | B607 | El ejecutable `git` se resuelve mediante PATH. Usar una instalación confiable; el control del PATH sigue siendo un riesgo residual. |
| `modeling/tracking.py:18` | B603 | Llamada sin shell, con argumentos definidos por el código y comprobación del resultado. Este módulo no incorpora el timeout del módulo de validación; una demora de Git sigue siendo una limitación operativa. |
| `validation/data_checks.py:20` | B404 | Importación de procesos utilizada únicamente para comprobar Git. |
| `validation/data_checks.py:49` | B603 | `rev-parse` usa el ejecutable resuelto, argumentos fijos, directorio del proyecto, timeout de 10 segundos y comprobación del código de salida. |
| `validation/data_checks.py:53` | B603 | `status` usa los mismos controles e incluye archivos nuevos; sus fallos producen estado no comprobado, nunca un repositorio declarado limpio. |
| `serving/verify_model.py:8` | B404 | Utilidad de comparación con un proceso independiente y código fijo; no es un endpoint de la API ni recibe órdenes de clientes. |

Los **tres avisos de validación** tienen su análisis detallado en
[seguridad_validacion.md](seguridad_validacion.md). Los cinco de entrenamiento
conservan el criterio documentado en [hallazgos.md](hallazgos.md), cuyo resto de
resultados permanece histórico. El aviso de `serving` pertenece a la Etapa 4 y se
explica en [seguridad_api.md](../etapa4/seguridad_api.md).

El análisis informa una exclusión específica preexistente de B603 en
`serving/verify_model.py`, respaldada por esa revisión: intérprete actual, código
fijo, ejecución aislada, sin shell y límite de tiempo. Esta comprobación no agregó
exclusiones ni modificó reglas. No se repitieron `pip-audit` ni Gitleaks, por lo que
no se atribuye una nueva auditoría de dependencias o secretos a este resultado.
`pip check` comprueba compatibilidad de paquetes, no ausencia de vulnerabilidades.

## Evidencia y datos históricos

- [Registro de PyTest](registros_20261107/pytest.txt): copia íntegra del contenido de
  consola, con rutas privadas, saltos de línea y espacios finales normalizados. El original y el JUnit
  permanecen locales; sus SHA-256 se incluyen en `estado_vigente.json`.
- [Registro del control de DeepChecks](registros_20261107/deepchecks_smoke.txt) y
  [resumen producido por la herramienta](registros_20261107/deepchecks_summary.json).
- [Captura original del caso variable](../figures/etapa3/cierre_20261107/deepchecks_variable.jpg)
  y [captura original del caso constante](../figures/etapa3/cierre_20261107/deepchecks_constante.jpg).
  Se tomaron directamente del HTML generado, sin retoque ni recomprimir. La cruz
  roja del segundo caso demuestra que el control detectó la anomalía introducida.
  Son controles sintéticos de compatibilidad, no una validación nueva de CSV reales.

La [validación real del 1 de noviembre](validacion_final_datos_20261101.json)
permanece sin cambios: **100 PASS, 3 WARN, 0 FAIL, 0 NOT_EVALUATED**, sobre
`03e114317db5e445f7905489b9a76f61b00e5b5e`. Su fecha UTC es el 2 de noviembre a
01:04:21, equivalente al 1 de noviembre en Ciudad de México. No se volvió a evaluar
el conjunto real de prueba, entrenar modelos oficiales ni modificar el Registry.

Los totales anteriores de 229, 238 y 245 corresponden a otras fechas y versiones.
Las 274 pruebas del 5 de noviembre fueron una recopilación de preparación, no una
ejecución aprobada. El total actual de 284 procede únicamente del JUnit de esta
ejecución, después de incorporar las diez pruebas del PR #56.

## Revisión y continuidad

Esta evidencia corresponde a [#53](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/53)
y requiere revisión independiente de Diego Hurtado. Para
[#54](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/54), Diego Hurtado
puede usar el resultado canónico y los registros enlazados para consolidar el README,
incorporar las capturas de PyTest y seguridad e identificar las aportaciones reales.
El resumen final deberá coincidir con el JSON. La revisión del
[PR #50](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/50)
es independiente de estas verificaciones.
