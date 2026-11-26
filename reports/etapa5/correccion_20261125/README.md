# Corrección del monitoreo de demanda

Versión del 25 de noviembre de 2026. Añade objetivo y predicción a Evidently y contrasta octubre de 2026 con octubre de 2025. Se conservan los modelos, el protocolo y las mediciones originales.

- [Informe editable](entrega/TC5061_Drift_ABTest_Equipo39.docx) y [PDF](entrega/TC5061_Drift_ABTest_Equipo39.pdf): cuatro páginas principales y cuatro anexos.
- [Interpretación directa](interpretacion.md) y [recomendación](recomendacion.md).
- [Reporte estacional de Evidently](drift_estacional.html) y [reporte histórico ampliado](drift_historico.html). Descargar el HTML y abrirlo en el navegador; GitHub no ejecuta su contenido interactivo.
- [Resumen numérico](resumen.json), [variables estacionales](drift_estacional_variables.csv), [variables históricas](drift_historico_variables.csv), [errores por segmento](error_segmentos.csv) y [serie diaria](demanda_diaria.csv).
- [Capturas originales](capturas/README.md), [manifiesto de predicciones](predicciones_manifiesto.json) y [verificación técnica](verificacion_tecnica.json).
- [Comandos de reproducción](../../../references/etapa5/correccion_estacional.md) y [responsables de revisión](colaboracion.md).
- [Informe anterior conservado](../entrega/TC5061_Drift_ABTest_Equipo39.pdf) y [comparación A/B original](../ab_resultados.json).

Resultado: demanda +58.31% contra ocho meses, +38.00% contra octubre anterior y +39.73% al estandarizar estación, día de semana y hora. A subestima 36.83% de las salidas actuales. La corrección requiere revisión independiente; las tareas #83, #84 y #85 siguen pendientes al preparar esta versión.
