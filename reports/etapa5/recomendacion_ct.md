# Recomendación de entrenamiento continuo

## Decisión para octubre de 2026

Conservar A en producción y mantener B como candidata. B mejora el MAE 2.46%, con un costo de ajuste bajo, pero no supera el umbral de utilidad de 5% y no satisface la condición de deterioro máximo en cuatro horas: 01:00, 02:00, 03:00 y 04:00. A la 01:00 el deterioro relativo es 44.00%; en las otras tres, A tiene MAE cero y B un error positivo muy pequeño, por lo que el porcentaje no está definido y la condición directa tampoco se cumple. La [tabla de segmentos](analisis_ab.md#estabilidad-y-segmentos) detalla los aumentos absolutos. La mejora estadística dentro de este mes no basta para justificar cambiar el servicio. Se conservan los umbrales y resultados originales.

El drift observado se concentra en mes y sus transformaciones. Es esperado al comparar ocho meses con un solo octubre, y estas variables no intervienen directamente en la media por estación-día-hora. La ausencia de alerta global tampoco garantiza precisión: el objetivo cambia y el MAE debe seguir observándose cuando estén disponibles los conteos reales.

## Operación propuesta

1. Al publicarse cada mes completo, descargarlo y comprobar huellas, columnas, días, duplicados, estaciones y ausencia de datos personales en la evidencia. Detener el proceso ante cambios de esquema, ausencia de días o alteración de una fuente ya fijada.
2. Generar el reporte de drift y evaluar el modelo vigente con las etiquetas observadas. Comparar cohortes y periodos equivalentes, incluyendo un diagnóstico del mismo mes del año anterior cuando sea posible.
3. Abrir una investigación si una alerta de drift persiste dos mensualidades o si el MAE empeora más de 10% frente a una referencia comparable. Son umbrales iniciales propuestos; todavía no están calibrados como alarmas operativas. Separar cambios reales de demanda de cambios de cobertura y de calidad.
4. Ante evidencia persistente, entrenar una candidata usando solo datos anteriores al periodo reservado para evaluación. Mantener una ventana de doce meses y estudiar, como experimento separado, una familia como Random Forest que pueda utilizar calendario e interacciones. No volver a usar octubre como prueba final de modelos elegidos después de conocer sus resultados.
5. Comparar en un mes posterior no utilizado, con los mismos pares, métricas, segmentos y mediciones de costo. La revisión independiente corresponde a Diego Hurtado; Marco resuelve observaciones y prepara la integración.
6. Promover solo con una decisión explícita respaldada por las métricas y la calidad. Conservar la versión anterior para reversión. La API de la etapa anterior empaqueta su modelo: cambiar el alias requiere además reconstruir y verificar el contenedor para que el servicio use la nueva versión.

## Estado de revisión y entrega

- Marco: código, resultados y nueve capturas integrados en `main` mediante el PR #64; reporte editable y PDF de cinco páginas preparados para revisión documental.
- Diego Hurtado: revisión técnica aprobada sobre `ebb45dc`, incluidas 52 pruebas y las nueve capturas. Queda revisar el nuevo reporte y su correspondencia con la evidencia aprobada.
- Stefania: aportación breve de interpretación (#62), abierta y no bloqueante; los contenidos necesarios ya están cubiertos por Marco y la revisión técnica de Diego Hurtado.
- Diego Martinez: ficha breve de linaje (#63), abierta y no bloqueante. La ficha técnica existente conserva las versiones, corridas y huellas.

Las aportaciones individuales pendientes no se atribuyen a quienes todavía no las han realizado. La aprobación técnica del PR #64 no se extiende automáticamente al nuevo documento. Se conserva A como `champion`, sin promoción automática.
