# Demanda y predicción con referencia estacional

La demanda observada de octubre de 2026 crece 58.31% respecto de octubre de 2025 a mayo de 2026. Al comparar únicamente octubre de 2025 con octubre de 2026, el aumento sigue siendo 38.00%. Ambas temporadas contienen las mismas 369 estaciones, 31 días y 274,536 filas estación-hora, incluidos los ceros. Las medias usan la población completa.

| Medida | Octubre 2025 a mayo 2026 | Octubre 2025 | Octubre 2026 |
|---|---:|---:|---:|
| Filas | 2,152,008 | 274,536 | 274,536 |
| Salidas observadas | 2,870,337 | 420,064 | 579,697 |
| Media observada por estación-hora | 1.333795 | 1.530087 | 2.111552 |
| Media predicha por A | 1.333795 | 1.349007 | 1.333844 |

El drift original de `month`, `month_sin` y `month_cos` era esperable al enfrentar ocho meses con un solo octubre. En el contraste entre octubres esas tres variables son constantes e iguales; ninguna de las nueve entradas rebasa el umbral de drift. Al ponderar por igual los 61,992 estratos estación × día de semana × hora, la demanda aumenta 39.73% y la predicción cambia 0.00%. Este ajuste controla la composición de días de semana, no todos los factores estacionales.

Evidently analiza 100,000 filas por conjunto, con semilla 39. Los nueve atributos conservan su alerta global (umbral 50% de atributos). Objetivo y predicción se evalúan con `ValueDrift` independiente y distancia de Wasserstein normalizada, umbral 0.1. El objetivo presenta drift histórico (0.322975) y estacional (0.218708); la predicción no lo presenta (0.005603 y 0.007398). Son distancias, no valores p. Las medias de la muestra pueden diferir ligeramente de las poblacionales.

La estabilidad de la predicción no demuestra que el modelo funcione bien. A conserva medias aprendidas por estación, día y hora y no ajusta automáticamente el nivel de demanda. En octubre de 2026 predice en promedio 0.777707 salidas menos por estación-hora; la subestimación agregada es 36.83% del total observado. Crecimiento y subestimación tienen denominadores diferentes: 38.00% compara dos periodos; 36.83% compara predicción con observación del periodo actual.

El sesgo puede llevar a planear menos bicicletas o movimientos de redistribución de los necesarios, especialmente donde coinciden demanda alta y error. Es una implicación operativa, no una medición de faltantes: los datos contienen viajes realizados, no inventario ni demanda insatisfecha. La estación 175 no registra salidas en octubre de 2026; sus ceros se conservan y no se imputan como actividad conocida.

Octubre de 2025 pertenece al entrenamiento de A. Su MAE descriptivo (0.809687) no es una prueba independiente de generalización ni permite atribuir causalmente el cambio de error al tiempo. Una sola comparación interanual tampoco demuestra concept drift: pueden influir crecimiento del sistema, eventos, clima o cambios operativos no medidos. El resultado firme es el aumento de salidas observadas y la subestimación de A en el periodo actual.

Fuentes: [resumen](resumen.json), [drift estacional](drift_estacional_variables.csv), [drift histórico](drift_historico_variables.csv), [errores por segmento](error_segmentos.csv) y [demanda diaria](demanda_diaria.csv). Los HTML originales de Evidently se conservan junto a estos archivos.
