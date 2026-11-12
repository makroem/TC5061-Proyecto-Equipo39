# Evidencia de monitoreo de P1

Resultados de Marco del 11 de noviembre de 2026. La integración está pendiente de revisión independiente de Diego Hurtado.

| Evidencia | Archivo |
|---|---|
| Reporte interactivo de Evidently | [drift.html](drift.html): descargar y abrir en el navegador; GitHub no lo ejecuta en la vista de código |
| Métricas de drift por variable | [drift_variables.csv](drift_variables.csv), con [JSON original](drift.json) |
| Calidad, cohortes y exclusiones | [datos_resumen.json](datos_resumen.json) y [calidad.json](calidad.json) |
| Interpretación del drift | [interpretacion_drift.md](interpretacion_drift.md) |
| Comparación, costo y estabilidad | [analisis_ab.md](analisis_ab.md), [ab_metricas.csv](ab_metricas.csv) y [ab_resultados.json](ab_resultados.json) |
| Gráfica de error diario | [error_diario.png](error_diario.png), obtenida de las observaciones evaluadas |
| Compatibilidad de firmas y entorno | [compatibilidad_modelos.json](compatibilidad_modelos.json), [entorno_evaluacion.json](entorno_evaluacion.json) |
| Entrenamiento de B y cierre de la corrida | [entrenamiento_b.json](entrenamiento_b.json), [cierre_corrida_b.json](cierre_corrida_b.json) |
| Recomendación y acciones siguientes | [recomendacion_ct.md](recomendacion_ct.md) |
| Pruebas y auditorías del cambio | [verificacion_tecnica.json](verificacion_tecnica.json), [bandit_monitoreo.json](bandit_monitoreo.json), [auditoria_dependencias.json](auditoria_dependencias.json) |

La revisión visual de Evidently se completó por Marco el 12 de noviembre de 2026. Las [cuatro capturas originales](capturas/README.md) muestran el resumen, la calidad, el detalle de mes y el reporte completo. Se verificó que sus cifras coinciden con los archivos publicados: tres de nueve variables con drift, proporción 0.333, sin alerta global y muestras de 100,000 filas por conjunto. Esta revisión no sustituye la validación independiente de Diego Hurtado.

Las capturas del Registry y de la comparación en la interfaz de MLflow siguen pendientes: el navegador integrado presentó errores al cargar archivos de la interfaz y el control de Chrome no pudo identificar con certeza la página activa. La consulta del servidor respondió correctamente; no se modificaron modelos, métricas ni alias. La gráfica de error diario continúa identificada como gráfica calculada, no como captura de interfaz. El reporte final de 3–5 páginas aún debe integrarse.

Los CSV de viajes, Parquet, modelos y bases de MLflow permanecen fuera de Git. Para reproducir el trabajo, consultar [las instrucciones concentradas](../../references/etapa5/reproduccion.md).
