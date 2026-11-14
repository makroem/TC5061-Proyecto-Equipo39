# Evidencia de monitoreo de P1

Resultados de Marco del 11 de noviembre de 2026. Diego Hurtado aprobó el commit `ebb45dc` el 12 de noviembre, hora de Ciudad de México; el [PR #64](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/64#pullrequestreview-5884278942) quedó integrado mediante `3fcca8a`.

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

La revisión visual de Evidently se completó por Marco el 12 de noviembre de 2026. Las [cuatro capturas originales](capturas/README.md) muestran el resumen, la calidad, el detalle de mes y el reporte completo. Se verificó que sus cifras coinciden con los archivos publicados: tres de nueve variables con drift, proporción 0.333, sin alerta global y muestras de 100,000 filas por conjunto. Diego Hurtado verificó posteriormente el reporte y la integridad de las nueve capturas, según su aprobación del PR #64.

Las cinco capturas originales de MLflow se completaron por Marco el 12 de noviembre de 2026: [versiones de P1](capturas/04_registry_p1_versiones.jpg), [A con alias champion](capturas/05_registry_a_champion_linaje.jpg), [B candidata](capturas/06_registry_b_candidata_linaje.jpg), [métricas pareadas de octubre](capturas/07_mlflow_comparacion_ab_octubre.jpg) y [trazabilidad de la evaluación](capturas/08_mlflow_trazabilidad_ab.jpg). Corresponden al registro existente y a la corrida `93f298b2c1404a8bb8a4eb1bed83b4bb`; no se modificaron modelos, métricas ni alias. La gráfica de error diario continúa identificada como gráfica calculada, no como captura de interfaz. La revisión técnica independiente quedó aprobada. El reporte de cinco páginas está disponible en [Word editable](entrega/TC5061_Drift_ABTest_Equipo39.docx) y [PDF](entrega/TC5061_Drift_ABTest_Equipo39.pdf), con formato Arial 11 e interlineado 1.15 en el cuerpo. La revisión documental de estos dos archivos permanece pendiente de Diego Hurtado; no se confunde con la aprobación técnica previa.

Los CSV de viajes, Parquet, modelos y bases de MLflow permanecen fuera de Git. Para reproducir el trabajo, consultar [las instrucciones concentradas](../../references/etapa5/reproduccion.md).
