# Protocolo de monitoreo y comparación de P1

## Pregunta y alcance

Se estima el número de salidas por estación-hora. A es la versión publicada del modelo `mibici-equipo39-p1-demanda`; su alias se resuelve una vez y se conserva la versión numérica y el run de origen. B actualiza la misma media estacional con doce meses. Mantener la familia permite estudiar el efecto de ampliar la ventana de entrenamiento. Una búsqueda con Random Forest requiere un experimento separado y no es condición de esta comparación.

La referencia son las filas de entrenamiento de A, del 1 de octubre de 2025 al 31 de mayo de 2026. B se ajusta desde el 1 de octubre de 2025 hasta el 30 de septiembre de 2026. Octubre de 2026 se reserva completo como conjunto actual. Los límites superiores de `protocolo.json` son exclusivos. Se conserva la partición temporal de la entrega publicada: los meses de validación/prueba antiguos pasan al entrenamiento de B de forma explícita; la evaluación nueva usa un mes posterior que ninguno de los dos modelos ha visto.

## Cohorte, calidad y trazabilidad

La elegibilidad se fija con el entrenamiento histórico: al menos 100 salidas por estación. Ambos modelos reciben las mismas claves estación-hora y los mismos objetivos de octubre. Solo se evalúan estaciones de esa cohorte presentes en el catálogo actual. Se reportan las estaciones y viajes externos a la cohorte, los viajes sin catálogo y las estaciones sin actividad observada. No se elimina una estación por tener error alto ni se eligen filas según el resultado de A o B.

Los CSV se descargan del portal oficial, conservando SHA-256 y tamaño. Las salidas históricas se verifican por su huella lógica contra el manifiesto confirmado y se contrastan con los objetivos preparados. Los datos nuevos se guardan en `data/monitoring/`, fuera de Git. Fechas, tipos, claves, conteos, calendario, valores faltantes y cobertura diaria se comprueban antes de evaluar.

Una hora sin viaje se interpreta como cero salidas para las estaciones del catálogo. Esto conserva la definición del objetivo histórico, pero no prueba que la estación haya estado operativa. Un día entero sin salidas detiene la preparación. La presencia de viajes todos los días tampoco demuestra que el proveedor haya publicado el 100% de los registros. Estas limitaciones deben acompañar la interpretación.

## Drift y evaluación

Evidently 0.7.23 se instala en un entorno independiente. El reporte utiliza las nueve variables de la firma. Estación, hora, día, mes y fin de semana son categóricas; las cuatro variables cíclicas son numéricas. Se usan Jensen–Shannon y Wasserstein normalizada, respectivamente, con umbral inicial 0.10 y fracción de variables con drift 0.50. Estos umbrales son decisiones iniciales, no límites operativos calibrados.

Se toma una muestra uniforme reproducible de hasta 100,000 filas por conjunto, con semilla 39. La calidad y la comparación A/B utilizan todas las filas. El mes y sus transformaciones están correlacionados; no se interpretan como tres evidencias independientes de deterioro. La media estacional usa estación, día y hora: un desplazamiento de mes no prueba por sí mismo que sus predicciones hayan empeorado.

La comparación es retrospectiva, pareada y fuera de línea. No es un experimento causal con usuarios ni reparto de tráfico. MAE es la métrica principal; RMSE complementa el costo de errores grandes. Se presenta mejora porcentual respecto de A; cuando el error de A es cero no se define un porcentaje. También se muestran errores por hora, fin de semana, estación y semana del mes. Los segmentos prioritarios para los umbrales son hora y fin de semana, definidos antes de consultar las métricas.

El intervalo exploratorio de MAE(B)−MAE(A) usa 1,000 remuestreos de bloques móviles de siete días, conservando todas las estaciones y los pares A/B de cada día. Se concatenan bloques hasta completar la longitud original. Octubre solo contiene pocos ciclos semanales: el intervalo no garantiza estabilidad futura ni causalidad.

La latencia se mide con lote de 1,000 filas, tres calentamientos y 30 repeticiones alternadas en el mismo equipo. Se informan mediana y percentil 95 del lote, no de una petición HTTP. Se mide el tiempo de ajuste de B. Si no existe tiempo comparable de entrenamiento de A, se declara no disponible.

## Decisión y continuidad

Una revisión favorable a B requiere mejora de MAE de al menos 5%, deterioro de RMSE no mayor a 2%, deterioro de MAE no mayor a 10% en segmentos prioritarios, intervalo superior de la diferencia de MAE menor que cero y latencia p95 no mayor a dos veces A. Son criterios para revisión, no una promoción automática. La calidad de fuentes y la incertidumbre operacional se revisan además de estas cifras.

Se mantiene `champion` sin cambios durante la preparación y comparación. Diego Hurtado revisa los resultados antes de integrar el trabajo. Un eventual cambio de alias requerirá decisión explícita, validación del servicio y posibilidad de reversión; una API que lleva el modelo empaquetado no cambia por modificar el alias.

La recomendación de entrenamiento continuo deberá usar la evidencia obtenida. Como punto de partida se propone revisión mensual, controles de calidad antes de entrenar y análisis de alertas persistentes, evitando reentrenar únicamente por cambios esperados del calendario.

## Referencias técnicas

- Evidently. (s. f.). *Report*. https://docs.evidentlyai.com/docs/library/report
- Evidently. (s. f.). *Customize data drift*. https://docs.evidentlyai.com/metrics/customize_data_drift
- MiBici. (s. f.). *Datos abiertos*. https://mibici.net/es/datos-abiertos/
- MLflow. (s. f.). *Model Registry*. https://mlflow.org/docs/latest/ml/model-registry/
