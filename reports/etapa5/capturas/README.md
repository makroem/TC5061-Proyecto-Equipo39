# Capturas originales de Evidently

Fecha: 12 de noviembre de 2026. Responsable de la evidencia: Marco.

Origen: `reports/etapa5/drift.html`, abierto mediante el servidor local `http://127.0.0.1:8765/drift.html`. Corresponde a los resultados generados el 11 de noviembre; la fecha de captura no representa una nueva ejecución del monitoreo.

| Archivo | Contenido y alcance |
|---|---|
| [01_evidently_resumen.jpg](01_evidently_resumen.jpg) | Resumen y nueve variables: tres con drift, proporción 0.333 y umbral global de 0.5. |
| [02_evidently_calidad.jpg](02_evidently_calidad.jpg) | Resumen de los dos conjuntos muestreados: 100,000 filas, nueve columnas, sin valores faltantes y tres columnas constantes en el conjunto actual. |
| [03_evidently_mes.jpg](03_evidently_mes.jpg) | Distribución de mes: el conjunto actual contiene octubre y la referencia incluye ocho meses. |
| [01_evidently_reporte_completo.jpg](01_evidently_reporte_completo.jpg) | Captura vertical completa, con resumen, calidad y perfiles de las nueve variables. Abrir la imagen original para consultar los detalles. |

Las imágenes son capturas directas del HTML renderizado en el navegador. Las tres primeras corresponden a regiones del reporte; la cuarta conserva la página completa. No se reconstruyeron tablas ni se editaron sus píxeles. Los archivos JPEG originales y sus dimensiones, huellas SHA-256 y regiones se conservan en [manifest.json](manifest.json).

## Interpretación

No se detecta drift global porque la proporción 3/9 es menor que el umbral 0.5. Sí se detectan cambios en `month`, `month_sin` y `month_cos`. La ausencia de alerta global no garantiza precisión del modelo. Las 100,000 filas por conjunto pertenecen al muestreo de drift; la evaluación A/B utiliza 274,536 observaciones y está documentada por separado.

## Alcance pendiente

Estas imágenes no muestran el Registry ni la comparación A/B de MLflow. Sus capturas siguen pendientes por errores de carga en la interfaz y por la interrupción del control de Chrome al no poder identificar con certeza la página activa. La revisión visual por Marco no equivale a la revisión independiente de Diego Hurtado ni a una aprobación del PR #64.
