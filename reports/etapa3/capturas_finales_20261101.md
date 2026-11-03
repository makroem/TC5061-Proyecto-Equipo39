# Capturas originales del cierre — Etapa 3

Fecha: 1 de noviembre de 2026, hora de Ciudad de México. Responsable: Marco.

El PR #38 fue aprobado e integrado por Diego Hurtado a las 20:38:58. Marco revisó el PR #39, contrastó los resultados con los registros originales y verificó sus 23 enlaces locales; la integración documental terminó a las 21:56:35. Los commits de integración son `fd28d965465cadd5a736253cace0b3c23c92820b` y `0bdf9880baab38926e89b823bdf1de2238fbdbec`, respectivamente.

Estas nueve imágenes se tomaron directamente del navegador y se guardaron sin retoques ni recompresión. El [manifiesto de capturas](capturas_finales_20261101.json) conserva fecha, dimensiones, procedencia y SHA256 de cada archivo, así como las huellas de los registros locales utilizados.

## Inventario

| ID | Archivo original | Qué acredita y alcance |
|---|---|---|
| F01 | [Integración del cierre técnico](../figures/etapa3/cierre_20261101/F01_PR38_integrado.jpg) | Página pública del PR #38; aprobado e integrado por Diego Hurtado. |
| F02 | [Integración documental](../figures/etapa3/cierre_20261101/F02_PR39_integrado.jpg) | Página pública del PR #39; revisado e integrado por Marco. |
| F03 | [Informe original de DeepChecks](../figures/etapa3/cierre_20261101/F03_DeepChecks_original.jpg) | Vista del HTML producido en la corrida final. Las tres cruces por columnas constantes se conservan; la política congelada las clasifica como WARN. |
| F04 | [Suite completa y cobertura](../figures/etapa3/cierre_20261101/F04_PyTest_registro_original.jpg) | Región de cobertura y resultado del registro original consultado en navegador: 238 aprobadas, 23 avisos; no es una consola en vivo. |
| F05 | [Linaje de la validación](../figures/etapa3/cierre_20261101/F05_Validacion_linaje_original.jpg) | Vista del resumen original: commit, versiones, partición, política congelada y fecha de ejecución. |
| F06 | [Totales y controles de integridad](../figures/etapa3/cierre_20261101/F06_Validacion_totales_original.jpg) | Vista del mismo resumen original: 100 PASS, 3 WARN, 0 FAIL, 0 NOT_EVALUATED y salida 0. |
| F07 | [Análisis estático de seguridad](../figures/etapa3/cierre_20261101/F07_Bandit_original.jpg) | Vista del JSON original de Bandit: ocho hallazgos bajos, ninguno medio o alto, sin errores ni pruebas omitidas. |
| F08 | [Auditoría de dependencias](../figures/etapa3/cierre_20261101/F08_Dependencias_resultado_publicado.jpg) | Captura del reporte estructurado ya publicado, sección proposed. Conserva los dos avisos de setuptools en DeepChecks; no es salida directa de pip-audit. |
| F09 | [Revisión de secretos](../figures/etapa3/cierre_20261101/F09_Gitleaks_registro_original.jpg) | Vista del registro original del escaneo: 118 commits disponibles, sin hallazgos. Corresponde al estado comprobado antes de integrar los PR #38 y #39. |

## Cómo interpretar las evidencias

F03 muestra el HTML original generado por DeepChecks. Las tres cruces señalan columnas constantes de P3 y se conservan tal como aparecen. El motor de calidad aplica la política congelada, que clasifica estas condiciones como advertencias; por ello F06 muestra 100 PASS, 3 WARN, 0 FAIL y 0 NOT_EVALUATED. La diferencia corresponde a la regla de clasificación del proyecto y no a una modificación de los resultados del HTML.

F04 muestra la región de cobertura y resultado del archivo original de PyTest. Se consultó el registro después de la ejecución, sin repetir las pruebas. La captura conserva las 238 pruebas aprobadas y los 23 avisos. El 82% de la salida de texto es un valor redondeado; el [JSON de la ejecución](revision_pr38_20261101.json) conserva 1,725 de 2,100 líneas cubiertas, equivalentes a 82.14%.

F05 y F06 muestran el mismo resumen original de validación, con su linaje y sus totales. F07 muestra la salida estructurada original de Bandit. F08 corresponde al [reporte de seguridad publicado](seguridad_cierre_20261101.json), no a una captura de consola de pip-audit. F09 muestra el registro original de Gitleaks y su alcance de 118 commits disponibles en aquel momento.

Las capturas se obtuvieron después de las ejecuciones. Las vistas de registros no deben describirse como una ejecución en vivo de consola. Los HTML y registros completos permanecen en el almacenamiento privado de calidad; sus copias de consulta se verificaron por SHA256. No se publican datos de viajes, modelos, bases de MLflow, credenciales ni entornos.

## Revisión y pendientes

Diego Hurtado revisó las nueve imágenes y confirmó su correspondencia con los reportes de cierre. El PR #40 fue aprobado e integrado en main el 1 de noviembre de 2026.

La captura F08 conserva los dos avisos presentes en aquella auditoría. El [cierre adicional de Marco](cierre_adicional_marco.md) documenta la solución posterior con setuptools 84.1.0 y la nueva auditoría sin vulnerabilidades conocidas, sujeta a revisión e integración. No se sustituyó F08 para aparentar que la ejecución anterior tenía ese resultado. No se repitió la validación final de datos ni se modificaron modelos, manifiestos o reglas de calidad.
