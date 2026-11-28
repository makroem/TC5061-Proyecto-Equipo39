# Recomendación de continuidad

Mantener temporalmente A como versión publicada y priorizar el desarrollo de una nueva candidata que responda al mayor nivel de demanda. Mantener A es una decisión de control de cambios; no significa que su subestimación de 36.83% sea aceptable para cualquier uso operativo.

La comparación A/B original se conserva: B reduce el MAE 2.46% y el RMSE 2.51%, pero no cumple la mejora mínima de MAE de 5% ni la regla por segmentos horarios. No se modifican los umbrales después de ver los resultados y no se promueve B automáticamente.

Para la siguiente candidata, investigar ventanas de entrenamiento recientes, ponderación temporal y variables operativas disponibles antes de la predicción. Verificar estaciones sin actividad y completitud de registros antes de atribuir todo el aumento al comportamiento de usuarios. Reservar un periodo posterior completo, todavía no empleado para ajustar decisiones, para la evaluación final. Octubre ya fue inspeccionado y no debe reutilizarse como nueva prueba independiente.

Comparar de forma pareada MAE, RMSE, sesgo agregado, errores por estación y hora y latencia bajo las mismas condiciones. Mantener las reglas de promoción existentes; cualquier regla adicional de sesgo debe acordarse y registrarse antes de evaluar la nueva candidata. Ejecutar validación temporal y revisión independiente, registrar el modelo como nueva versión y conservar un mecanismo de reversión.

Monitorear en cada periodo cerrado tres señales separadas: entradas frente a la misma temporada, objetivo cuando lleguen sus etiquetas y predicción. La ausencia de drift en las entradas o en la predicción no cancela una alerta de demanda ni sustituye medir el error. No se reentrenó, no se cambió el alias y no se alteraron las mediciones originales en esta corrección.
