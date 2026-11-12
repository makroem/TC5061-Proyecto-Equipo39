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

## Pendientes de revisión

- Diego Hurtado: revisar el código, el resultado pareado, la documentación del costo y las limitaciones; aportar revisión al PR.
- Stefania: revisión breve de la interpretación del drift (#62), con respaldo de Marco y validación de Diego Hurtado.
- Diego Martinez: ficha breve de linaje A/B (#63), con el mismo respaldo. No debe ejecutar infraestructura ni entrenamientos.
- Marco y Diego Hurtado: completar las capturas del Registry y de la comparación en MLflow e integrar el reporte final de 3–5 páginas. Las cuatro capturas originales de Evidently y su revisión visual por Marco se completaron el 12 de noviembre; la revisión independiente permanece pendiente. El control de Chrome se detuvo al no poder identificar con certeza la página activa.

Ninguna tarea documental de Stefania o Diego Martinez bloquea la preparación, la comparación ni la integración técnica revisada. La revisión independiente del PR sí se conserva.
