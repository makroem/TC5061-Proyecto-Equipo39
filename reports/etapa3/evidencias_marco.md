# Evidencia preliminar de Marco — Etapa 3

Ejecuciones del 28 de octubre de 2026. Las imágenes son capturas de navegador.
E04 y E05 muestran los HTML originales de DeepChecks con datos sintéticos.
Las otras seis muestran registros exportados de ejecuciones reales, identificados
como tales en cada página; no son capturas directas de una consola.

| Archivo | Qué muestra | Límite de la evidencia |
|---|---|---|
| [E01: entornos](../figures/etapa3/E01_entornos.jpg) | Versiones del entorno de calidad y del entorno independiente | No certifica todos los checks de datos reales |
| [E02: estructura](../figures/etapa3/E02_estructura.jpg) | Inventario inicial de archivos versionados de pruebas | Snapshot del commit probado; archivos de evidencia posteriores no aparecen allí |
| [E03: ingesta](../figures/etapa3/E03_ingesta.jpg) | 43 pruebas aprobadas y cobertura de ingesta | Extracto del registro de ejecución |
| [E04: control positivo](../figures/etapa3/E04_deepchecks_variable.jpg) | DeepChecks acepta la columna variable | Fixture sintético de compatibilidad |
| [E05: control negativo](../figures/etapa3/E05_deepchecks_constante.jpg) | DeepChecks detecta la columna constante | El rechazo es intencional y confirma que la condición funciona |
| [E06: suite completa](../figures/etapa3/E06_suite_sintetica.jpg) | 155 pruebas aprobadas y cobertura global | No sustituye el cierre integrado posterior |
| [E09: seguridad](../figures/etapa3/E09_seguridad.jpg) | Análisis estático, historial y avisos de dependencias | Diagnóstico preliminar con hallazgos abiertos |
| [E10: exclusiones](../figures/etapa3/E10_exclusiones.jpg) | Reglas comprobadas con `git check-ignore` | El escaneo del snapshot complementa esta comprobación |

La numeración conserva los identificadores del plan de evidencia. No se inventaron
capturas para las actividades que aún dependen del equipo. Los resultados de datos
reales y el cierre final deben añadirse después de ejecutar esas actividades.

El [manifiesto de evidencia](evidencias_manifest.json) contiene los hashes SHA256,
origen y fecha de cada captura. El código de las pruebas corresponde al commit
`b00703251085ada10693d5b31fc69b99ab6640ae`. Los archivos de entorno y compatibilidad
publicados después se identifican además mediante su propio hash.

Los comandos para repetir las comprobaciones están en
[ejecucion_marco.md](../../references/etapa3/ejecucion_marco.md) y
[deepchecks_entorno.md](../../references/etapa3/deepchecks_entorno.md).
Los registros completos, temporales y HTML originales se conservan en
`private_quality/`, excluido de Git; las versiones públicas contienen solo resultados
revisados. No se publican CSV de MiBici, modelos, bases de MLflow ni valores de credenciales.

## Actualización posterior: dependencias

[E12: actualización parcial](../figures/etapa3/E12_actualizacion_dependencias.jpg)
documenta la ejecución del commit `8b63701a158d6ab9191143f3283bcc18fd5a9022`
con cuatro versiones corregidas. Es una captura de un registro exportado de
resultados reales, identificada como tal. La suite aprobó 155 pruebas y la auditoría
redujo de seis a dos los paquetes con avisos. MLflow y PyArrow continúan pendientes.
Sus hashes y fuentes están en
[actualizacion_dependencias.json](actualizacion_dependencias.json); esta captura
complementa las ocho anteriores y no modifica sus resultados históricos.
