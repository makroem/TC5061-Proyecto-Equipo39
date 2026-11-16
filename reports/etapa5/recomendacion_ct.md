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

- Marco: código, resultados y nueve capturas integrados mediante el PR #64; versión inicial del reporte integrada mediante el PR #65, commit `21723ad`. La ampliación actual reúne cinco páginas principales, incluida la portada, y cinco de anexos, con su [verificación documental](entrega/verificacion_reporte.json).
- Diego Hurtado: revisión técnica aprobada sobre `ebb45dc`, incluidas 52 pruebas y las nueve capturas; revisión documental completada sobre `aea5e5e`, según la [aprobación del PR #65](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/65#pullrequestreview-5905311387). La observación de interlineado quedó resuelta.
- Stefania: interpretación presentada en el [PR #68](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/68). La interpretación de cohorte y calendario fue corregida en `c0c8c84`; Marco solicitó ajustar la extensión y convertir las tres referencias en enlaces. La tarea #62 sigue abierta; esta corrección documental no bloquea la entrega técnica.
- Diego Martinez: [ficha de linaje](revision_linaje_diego_martinez.md) revisada y aprobada por Marco sobre `a6b5984`, e integrada mediante el [PR #67](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/67), commit `9db8082`, el 15 de noviembre. La tarea #63 quedó cerrada. La revisión delimita la evidencia publicada y las comprobaciones que requerirían acceso al Registry y a los Parquet.

El estado anterior distingue aportaciones presentadas, correcciones solicitadas e integración, conservando la autoría de cada persona. La aprobación del PR #65 corresponde al reporte anterior de cinco páginas sin anexos; la ampliación actual requiere revisión documental propia. La aprobación técnica del PR #64 se conserva. Se conserva la decisión de mantener A como `champion`, sin promoción automática.
