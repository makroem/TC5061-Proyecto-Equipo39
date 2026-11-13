# Interpretación inicial del drift de P1

Se compararon 100,000 filas muestreadas de las 2,152,008 filas de referencia y 100,000 de las 274,536 filas actuales, con semilla 39. Los conjuntos completos cubren 369 estaciones. El reporte se encuentra en `drift.html` y sus métricas en `drift.json`; `drift_variables.csv` facilita la revisión por variable.

Tres de las nueve variables superan el umbral individual: mes y sus dos transformaciones cíclicas. La fracción es 33.3%, inferior al umbral global de 50%. Por lo tanto, no se activa la alerta global definida en este protocolo. Esto no equivale a certificar que el modelo siga siendo preciso.

La referencia contiene ocho meses y el conjunto actual contiene solo octubre. El desplazamiento del calendario es esperado y las tres variables afectadas son transformaciones de una misma señal; no constituyen tres causas independientes. El modelo A utiliza medias por estación, día y hora, con respaldo por estación-hora y media global. Su predicción no utiliza directamente el mes ni sus senos y cosenos, aunque estas variables forman parte de la firma.

La distribución de variables de calendario de una malla completa es casi uniforme por construcción. Que estación u hora no muestren drift no implica que las salidas observadas sean constantes. La demanda media pasa de aproximadamente 1.33 salidas por estación-hora en la referencia a 2.11 en octubre. El cambio del objetivo y el desempeño se estudian por separado mediante MAE, RMSE y errores por segmento en la comparación A/B.

Se conservaron 635,532 viajes en la limpieza del CSV actual. De ellos, 55,835 salidas quedan fuera de la cohorte de evaluación; una salida corresponde a un identificador ausente del catálogo actual. La estación 175 permanece en el catálogo y en la cohorte, pero no registra salidas en octubre. Se mantiene en la evaluación primaria, sin inferir una causa de cierre o indisponibilidad que estos datos no permiten comprobar. Estas circunstancias limitan la generalización a toda la red.

Evidently emitió advertencias de división al calcular correlaciones con variables constantes del mes actual. Esas correlaciones no están definidas; no se interpretan como cero. Los estadísticos de drift por variable se generaron y sus valores se conservan en el JSON. La revisión final debe comprobar estas limitaciones junto con el desempeño antes de recomendar reentrenamiento o promoción.

Estado: análisis preliminar de Marco, pendiente de revisión documental de Stefania o del respaldo Marco/Diego Hurtado. Las conclusiones de desempeño dependen de la comparación pareada, no de esta alerta de drift por sí sola.
