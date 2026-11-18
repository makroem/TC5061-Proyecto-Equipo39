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

- Marco: código, resultados y nueve capturas integrados mediante el PR #64; versión inicial del reporte mediante el PR #65. La ampliación de diez páginas fue aprobada por Diego Hurtado sobre `178afc9` e integrada mediante el [PR #70](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/70), commit `8bd3194`, el 16 de noviembre de 2026.
- Diego Hurtado: revisión técnica del PR #64 y revisión del reporte inicial del PR #65 completadas; también aprobó la [aportación de Stefania sobre `f67b4e4`](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/68#pullrequestreview-5914861787) y la [ampliación del reporte sobre `178afc9`](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/70#pullrequestreview-5914925420).
- Stefania: [interpretación del drift](revision_interpretacion_stefania.md) integrada mediante el [PR #68](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/68), commit `ab35051`, después de la revisión independiente. La tarea #62 está cerrada.
- Diego Martinez: [ficha de linaje](revision_linaje_diego_martinez.md) integrada mediante el [PR #67](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/67), commit `9db8082`. La tarea #63 está cerrada; se conservan los límites de su revisión documental.

El [cierre documental](cierre_documental.md) registra las aprobaciones y las integraciones, conservando la autoría y el alcance de cada aporte. El anexo D del reporte y los estados de la verificación describen el momento de su preparación; las aprobaciones posteriores no modifican los archivos ya revisados. Se conserva la decisión de mantener A como `champion`, sin promoción automática.
