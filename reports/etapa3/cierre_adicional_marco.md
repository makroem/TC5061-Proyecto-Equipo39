# Cierre adicional de compatibilidad y evidencia

Fecha de ejecución: 1 de noviembre de 2026, Ciudad de México.
Responsable de esta aportación: Marco.
Base revisada: `5344be3498bd3d46459c7e905e341fd6f5aec0c2`.

La actualización resuelve la incompatibilidad que obligaba a conservar setuptools
81.0.0 en el entorno separado de DeepChecks. Con setuptools 84.1.0, las 245 pruebas
del proyecto aprobaron sin fallos ni omisiones y la auditoría de sus 122 requisitos
no encontró vulnerabilidades conocidas. También se renovó una captura histórica
de MLflow y sus copias en la propuesta de la primera entrega.

Los resultados y hashes están en [el registro de esta ejecución](cierre_adicional_marco.json).
La [salida original de pip-audit](auditoria_deepchecks_20261101.json) enumera los
122 paquetes revisados. Esta aportación requiere revisión independiente antes de
integrarse en `main`.

## Compatibilidad de DeepChecks

DeepChecks 0.19.1 importa `pkg_resources` en dos utilidades de presentación. La
adaptación de [prepare_deepchecks.py](../../scripts/prepare_deepchecks.py) utiliza
`importlib.metadata` para consultar paquetes y `packaging.version.parse` para
comparar versiones. Esto permite instalar setuptools 84.1.0 y atender los avisos
`PYSEC-2026-3447` y `GHSA-xmj3-9gf7-h52w` documentados en la revisión anterior.

El script solo admite DeepChecks 0.19.1. Comprueba los hashes de ambos archivos
antes de escribir, rechaza cambios inesperados y permite repetir la preparación
sin modificar otra vez el contenido. Conserva los avisos de licencia e identifica
la adaptación local. La fecha de esa nota está expresada en UTC. No se presenta
como una versión publicada por el proveedor.

El entorno se creó desde cero con Python 3.11.9. Las 122 versiones instaladas
coinciden con las declaradas, incluida `win32-setctime`, ahora fijada de forma
explícita para Windows. No se instala este archivo de requisitos en el entorno de
entrenamiento. La [guía de DeepChecks](../../references/etapa3/deepchecks_entorno.md)
documenta la comprobación previa, instalación, adaptación y validación.

## Resultados comprobados

| Comprobación | Resultado | Alcance |
|---|---|---|
| Instalación independiente | 122 versiones coincidentes; `pip check` aprobado | Windows x86-64 y Python 3.11.9 |
| Dependencia retirada | `pkg_resources` no está disponible; DeepChecks importa correctamente | Setuptools 84.1.0 |
| Adaptación repetida | Segunda ejecución sin cambios | Dos archivos verificados por SHA256 |
| Pruebas nuevas | 7 aprobadas | Idempotencia, versiones incompatibles, archivos ausentes o alterados y sustituciones ambiguas |
| Suite completa | **245 aprobadas; 0 fallos, 0 errores, 0 omisiones; 23 avisos** | 448.62 segundos, datos sintéticos y recursos temporales |
| Control de DeepChecks | Caso variable aprobado; caso constante rechazado, como se esperaba | Importación, comprobación y exportación de ambos HTML |
| Motor de calidad | Casos reales de uso de la biblioteca incluidos en la suite | Controles positivo y negativo en el entorno separado |
| Auditoría de dependencias | **0 vulnerabilidades conocidas en 122 paquetes**, sin paquetes omitidos | Consulta de versiones fijadas, salida 0 |
| Bandit sobre el script nuevo | 0 hallazgos y 0 errores en 75 líneas | No sustituye el análisis histórico del resto del módulo |

La suite utilizó el entorno de calidad previamente validado y el código de esta
rama; DeepChecks utilizó su entorno nuevo. No se recalculó cobertura: el 82.14%
publicado anteriormente corresponde a la ejecución histórica de 238 pruebas.
Los 23 avisos se conservan en los registros de ejecución.

## Renovación de la captura histórica

Se consultó la corrida `cfa19d964f654a98b432c60ecb6effc3`, P1 baseline, mediante
MLflow 3.17.2. Para la consulta se utilizó una copia de la base migrada y se
configuró en esa copia la ruta del artefacto mediante el servidor de MLflow.
La base de origen permanece intacta. No se modificaron métricas, parámetros,
etiquetas ni contenidos de los artefactos.

Los cinco archivos de la corrida coinciden byte por byte con el origen. La figura
`figures/p1_mae_por_hora.png` conserva el SHA256
`87180dc3898fc67b78afdfc66835439958f66bd32544958649d92bcb4d8d2925`.

La [captura original actualizada](../../references/evidence/03_artefacto_mlflow.jpg)
se guardó directamente desde la interfaz, sin retocar su contenido. La misma imagen
se incorporó al Anexo 4 del [Word editable](../TC5061_Propuesta_Proyecto_Equipo39.docx)
y del [PDF](../TC5061_Propuesta_Proyecto_Equipo39.pdf). El pie indica la fecha y
versión de la consulta. Se revisaron visualmente las 18 páginas del PDF.

En el Word solo cambió esa imagen y su pie. La exportación a PDF conserva las
18 páginas y los resultados; además del pie, la extracción de texto solo refleja
un salto de línea diferente en dos enlaces de referencias. Los estados de PR,
fechas y resultados de la propuesta siguen siendo el registro histórico del
18 de octubre, no una descripción del estado actual del proyecto.

## Reproducción

Seguir primero la [guía de instalación](../../references/etapa3/deepchecks_entorno.md).
Desde la raíz del repositorio, con ambos entornos preparados:

```powershell
.\.venv-deepchecks\Scripts\python.exe scripts/prepare_deepchecks.py
.\.venv-deepchecks\Scripts\python.exe -m pip check
.\.venv-deepchecks\Scripts\python.exe scripts/check_deepchecks_env.py
.\.venv-a7\Scripts\python.exe -m pytest tests -q
.\.venv-a7\Scripts\python.exe -m pip_audit -r requirements-deepchecks.txt --no-deps --disable-pip --progress-spinner off
.\.venv-a7\Scripts\python.exe -m bandit scripts/prepare_deepchecks.py
```

Revisar `$LASTEXITCODE` después de cada comando y detenerse ante un resultado
distinto de cero. En Windows, la guía general explica el uso de rutas temporales
cortas y el límite de hilos para las pruebas. Una reinstalación de DeepChecks
requiere repetir su preparación.

## Alcance y revisión pendiente

La validación final de datos reales conserva su resultado original: 100 PASS,
3 WARN, 0 FAIL y 0 NOT_EVALUATED. No se repitió para ajustar criterios. Se mantienen
la política congelada, los manifiestos y los modelos. Las observaciones bajas de
Bandit del módulo original siguen documentadas; una auditoría sin avisos conocidos
no garantiza ausencia de todos los riesgos.

| Actividad | Responsable | Estado o dependencia |
|---|---|---|
| Corrección compatible de dependencias | Marco | Implementada y verificada en esta rama |
| Actualización de captura, Word, PDF y seguimiento | Marco | Completada en esta rama |
| Revisión independiente de los cambios | Otro integrante con permisos de revisión | Revisar código, resultados y evidencia antes de aprobar |
| Integración en `main` | Marco o integrante autorizado | Depende de la aprobación y las reglas de la rama protegida |

Los registros completos, HTML, base de consulta y entornos permanecen fuera de Git.
Se conservan hashes para contrastar la evidencia. Los reportes anteriores mantienen
sus resultados y fechas; este documento actualiza el estado de sus dos avisos de
dependencias sin reescribir el historial.
