# Verificación integrada de Marco — Etapa 3

Fecha: 1 de noviembre de 2026, hora de Ciudad de México.
Repositorio: [TC5061-Proyecto-Equipo39](https://github.com/makroem/TC5061-Proyecto-Equipo39).
Código integrado comprobado: `03e114317db5e445f7905489b9a76f61b00e5b5e`.

Después de integrar los PR #33, #35 y #37, ejecuté las comprobaciones desde un clon nuevo. Los dos entornos se instalaron con Python 3.11.9. El repositorio estaba limpio antes y después de la ejecución. Se conservaron los registros originales, incluidos los avisos y el intento de instalación que falló por la longitud de la ruta en Windows.

## Resultados

| Comprobación | Resultado | Alcance |
|---|---|---|
| Suite completa de PyTest | 238 aprobadas; 0 fallos, errores u omisiones; 23 avisos | Código integrado, datos sintéticos y recursos temporales |
| Cobertura global | 1,725 de 2,100 líneas: 82.14 % | Módulo completo; ninguna línea excluida del cálculo |
| Validación final de datos | 100 PASS, 3 WARN, 0 FAIL y 0 NOT_EVALUATED; salida 0 | P1, P2 y P3; train, validation y test |
| Política de calidad | Versión 1, congelada; hash sin cambios | No se ajustaron reglas ni umbrales después de consultar test |
| Datos preparados | 155 archivos copiados y comparados por SHA256 | La validación contrastó además los 151 hashes lógicos del manifiesto |
| Instalación de los dos entornos | Versiones fijadas coincidentes y `pip check` aprobado | Entorno de calidad y entorno independiente de DeepChecks |
| Secretos en historial | Sin hallazgos en 115 commits analizados | Referencias disponibles en el clon; incluye el PR #37 |
| Bandit | 8 observaciones bajas; 0 medias y 0 altas | Observaciones conservadas y explicadas en el reporte de seguridad |

La suite terminó a las 19:10:59. La corrida final de datos se inició a las 18:50:33 y produjo su resumen a las 19:04:21. Se ejecutó una sola vez sobre datos reales con la política congelada.

Los resultados detallados y las huellas de los registros están en [cierre_integrado_marco_20261101.json](cierre_integrado_marco_20261101.json). El [resumen original de validación](validacion_final_datos_20261101.json) conserva las 103 comprobaciones, sus criterios y resultados.

## Datos y advertencias de P3

Se usó la versión de datos `e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7` y la partición `ab6301f96f083217512343b4f800bc5ddea51b666492ef05b34da85591cc9bdd`.

La descarga anual no se repitió. Se copiaron las tablas procesadas existentes al clon nuevo, se compararon los archivos y se ejecutó el control de linaje del motor. El catálogo de estaciones coincidió con el manifiesto oficial en Windows x86-64. El resultado previo de macOS ARM permanece documentado como antecedente; no se cambió el manifiesto.

Las tres advertencias corresponden a columnas constantes en los perfiles de P3:

- Train: seis columnas de las horas 02, 03 y 04, entre semana y fin de semana.
- Validation: `weekday_hour_03`.
- Test: `weekday_hour_02`, `weekday_hour_03`, `weekend_hour_02`, `weekend_hour_03` y `weekend_hour_04`.

La política clasifica estas condiciones como advertencias. Se conservan para interpretar los perfiles; no se eliminaron columnas ni se modificaron los modelos para conseguir un resultado favorable.

## Corrección adicional de dependencias

La auditoría detectó cuatro avisos en `pyasn1 0.6.4` y avisos adicionales en las herramientas de instalación heredadas. La propuesta actualiza `pyasn1` a 0.6.5, `pip` a 26.2, `setuptools` a 84.1.0 y `wheel` a 0.46.2 en los entornos compatibles. El archivo de MLflow Projects y el entorno de calidad conservan las mismas versiones de esas herramientas.

Se instaló la propuesta después de terminar la suite base. Los 154 requisitos del entorno de calidad coincidieron con las versiones fijadas y `pip check` pasó. Con esas versiones se ejecutaron las pruebas de MLflow Projects y migración: **23 aprobadas, 0 fallos y 14 avisos**. También se construyó e instaló el paquete en un entorno nuevo. Estos controles no se presentan como otra ejecución de las 238 pruebas ni como un reentrenamiento.

La auditoría de la propuesta no encontró avisos conocidos en los 132 requisitos del proyecto, los 22 requisitos adicionales de calidad ni las tres herramientas declaradas de construcción. Se revisaron por separado porque el auditor no incorpora automáticamente todos los archivos referenciados con `-r` en el modo utilizado.

DeepChecks conserva `setuptools 81.0.0`, necesario para su uso de `pkg_resources`. En sus 121 requisitos permanecen **dos avisos únicos**, reportados en tres entradas: `PYSEC-2026-3447` y `GHSA-xmj3-9gf7-h52w`. Se actualizó `pip` y se comprobó compatibilidad, sin repetir la corrida final. Este entorno queda dedicado a validación, sin construir o publicar distribuciones ni usar instalaciones heredadas. Estas restricciones no eliminan los avisos. Marco y Diego Martinez deben evaluar una solución compatible antes de declararlos cerrados.

El [reporte de seguridad](seguridad_cierre_20261101.json) conserva los resultados anteriores y propuestos, versiones, identificadores y huellas de los registros. La corrección de `pyasn1` está descrita por sus mantenedores en la [publicación 0.6.5](https://github.com/pyasn1/pyasn1/releases/tag/v0.6.5).

## Cómo reproducir las comprobaciones

Usar una ruta corta en Windows y seguir primero las [instrucciones de comprobación e instalación](../../references/etapa3/ejecucion_marco.md). Mantener separados los entornos de calidad y DeepChecks. Desde la raíz del repositorio:

```powershell
.\.venv-a7\Scripts\python.exe -m pip check
.\.venv-deepchecks\Scripts\python.exe -m pip check
.\.venv-a7\Scripts\python.exe -m pytest tests -q
.\.venv-deepchecks\Scripts\python.exe -m mibici_equipo39.validation.data_checks --question all --stage final
.\.venv-a7\Scripts\python.exe -m pip_audit -r requirements.txt --no-deps --disable-pip --progress-spinner off
.\.venv-a7\Scripts\python.exe -m pip_audit -r requirements-quality.txt --no-deps --disable-pip --progress-spinner off
.\.venv-a7\Scripts\python.exe -m pip_audit -r requirements-deepchecks.txt --no-deps --disable-pip --progress-spinner off
.\.venv-a7\Scripts\python.exe -m bandit -r mibici_equipo39
```

La etapa `final` requiere las tablas oficiales y la política congelada. Los comandos anteriores documentan la reproducción; no son una indicación de repetir la evaluación de test para ajustar criterios. Una auditoría con salida 1 y hallazgos requiere interpretación, no ocultar su resultado.

## Evidencias y pendientes

Los JSON publicados son reportes de ejecución. El HTML original de DeepChecks y los registros completos permanecen en el almacenamiento local de calidad. No se publican tablas de MiBici, modelos, bases de datos ni archivos de entornos.

Las capturas directas nuevas del cierre aún no están incorporadas. Las imágenes anteriores conservan su fecha y alcance; no se reutilizan como prueba de esta ejecución.

| Responsable | Pendiente | Dependencia |
|---|---|---|
| Diego Hurtado | Revisar el PR #38 de correcciones y cierre de Marco | Cambios y evidencias publicados en la rama de revisión |
| Marco | Incorporar las capturas directas del cierre | Disponibilidad de captura de las ventanas con resultados reales |
| Diego Hurtado | Completar la consolidación visual y sus enlaces | Capturas nuevas y resultados de este cierre |
| Marco y Diego Martinez | Dar seguimiento a los dos avisos del entorno DeepChecks | Una solución compatible; los avisos siguen abiertos |

El PR #37 de Diego Hurtado fue revisado por Marco e integrado después de comprobar 46 enlaces locales y contrastar las cifras con los reportes de origen. La evidencia de colaboración conserva la autoría y las revisiones de cada integrante.
