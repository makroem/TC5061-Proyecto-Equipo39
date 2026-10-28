# Búsquedas oficiales de Marco - Etapa 2

Estado al 27 de octubre de 2026: búsquedas verificadas y selecciones aprobadas por los responsables de P1, P2 y P3, integradas mediante el PR #22. La reproducción y el registro posteriores están comprobados en el [cierre técnico](cierre_tecnico_marco.md). Las tablas de este documento conservan las métricas de las búsquedas originales.

La ingesta descargó nuevamente los doce meses desde un clon nuevo. Se conservaron 4,497,119 de 4,497,877 viajes y se construyeron 4,108,440 filas de estación por hora. La partición conserva 243 días de entrenamiento, 61 de validación y 61 de prueba.

Versión de datos: `e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7`.
Partición: `ab6301f96f083217512343b4f800bc5ddea51b666492ef05b34da85591cc9bdd`.

Cada pregunta tiene un padre y cuatro hijas finalizadas: baseline y tres candidatos. Se comprobaron los doce modelos guardados, sus firmas, ejemplos y predicciones al recargarlos, manifiestos, configuraciones y gráficas. P1 incluye los CSV de error por mes y hora.

## Comparación y propuestas de selección

### P1

Commit: `97f0033d1669bea64f38d86cf78f680dffbd3062`. Padre: `310ec0be030047fc851669c8e91d863c`.

| Variante | Validación | Prueba | Diferencia favorable en validación |
|---|---:|---:|---:|
| baseline | 0.888775 | 0.916381 | +0.000000 |
| p1_hgb_100 | 0.985315 | 0.997964 | -0.096540 |
| p1_hgb_200 | 0.909733 | 0.931749 | -0.020957 |
| p1_rf_300 | 0.919891 | 0.935562 | -0.031116 |

Métrica: mae. Propuesta automática: `baseline`, corrida `0a540d20ad8d4edc8290a85c64de79f1`.
Regla aplicada antes de evaluar prueba: menor val_mae entre elegibles; empate a 6 decimales lo gana el baseline.

La tabla `p1_comparacion_oficial.csv` conserva hiperparámetros y todas las métricas registradas.

En esta ejecución, los tres candidatos tuvieron mayor MAE de validación que el baseline. El bosque requirió 1268.95 segundos de ajuste y 425.64 MB serializados. HGB 100 tuvo RMSE de validación 7.667411, frente a 1.696415 del baseline; sus errores extremos merecen revisión.

El baseline se conserva si su MAE de validación es menor o empata a seis decimales. Una alternativa más costosa debe justificar su mejora. Revisar también RMSE y error por mes y hora para localizar errores extremos.

Responsable de revisar el análisis y la propuesta: Stefania.

### P2

Commit: `97f0033d1669bea64f38d86cf78f680dffbd3062`. Padre: `e0d9f693f211405ba3dcd80b357be4cb`.

| Variante | Validación | Prueba | Diferencia favorable en validación |
|---|---:|---:|---:|
| baseline | 0.000000 | 0.000000 | +0.000000 |
| p2_lr_0.1 | 0.042360 | 0.052181 | +0.042360 |
| p2_lr_1 | 0.042048 | 0.051779 | +0.042048 |
| p2_lr_10 | 0.041985 | 0.051701 | +0.041985 |

Métrica: macro_f1. Propuesta automática: `p2_lr_0.1`, corrida `b24e7ffdf7524a96914dbe1e0fa7f356`.
Regla aplicada antes de evaluar prueba: mayor val_macro_f1 entre elegibles; empate a 6 decimales lo gana el baseline.

La tabla `p2_comparacion_oficial.csv` conserva hiperparámetros y todas las métricas registradas.

En el código, val_macro_f1 es el promedio de los F1 de la clase positiva de bicicletas y anclajes; no es un promedio entre las clases negativa y positiva de un solo clasificador.

La mejora absoluta de validación es 0.042360; no se calcula mejora porcentual al ser cero el baseline. En prueba, la precisión fue 2.19% para bicicletas y 3.21% para anclajes, con recall 0.8495 y 0.7898. Estos resultados requieren valorar la carga de falsas alertas y no demuestran utilidad operativa.

La comparación utiliza F1 macro de validación con umbrales calibrados exclusivamente en validation. La calibración propuesta se conserva en selection.json para reproducirla sin optimizarla de nuevo. El riesgo es un proxy sin inventario observado. Una precisión registrada como cero cuando no hay alertas es una convención numérica y no una precisión operativa medible. Revisar recall, precisión, prevalencia y alertas por mil de ambos riesgos antes de aceptar el uso operativo.

Responsable de revisar el análisis, la calibración y la propuesta: Diego Martinez.

### P3

Commit: `97f0033d1669bea64f38d86cf78f680dffbd3062`. Padre: `09bfe57afcea4438b67aa7afc37ed56d`.

| Variante | Validación | Prueba | Diferencia favorable en validación |
|---|---:|---:|---:|
| p3_kmeans_3 | 0.005564 | 0.079255 | +0.000000 |
| p3_kmeans_4 | -0.019898 | 0.028182 | -0.025461 |
| p3_kmeans_5 | -0.043167 | 0.027266 | -0.048731 |
| p3_gmm_3 | 0.026594 | 0.051373 | +0.021030 |

Métrica: silhouette. Propuesta automática: `p3_gmm_3`, corrida `46ce752d830c4edfbbb6cd7e05aabc86`.
Regla aplicada antes de evaluar prueba: mayor val_silhouette entre elegibles; empate a 6 decimales lo gana el baseline.

La tabla `p3_comparacion_oficial.csv` conserva hiperparámetros y todas las métricas registradas.

La propuesta obtiene silhouette de prueba 0.051373, menor que 0.079255 del baseline. No se cambia la elección después de observar prueba. El ARI medio de remuestreo de entrenamiento es 0.491616; el grupo mínimo en prueba baja a 4.61%. Son limites de estabilidad y separacion que deben interpretarse antes de usar los grupos para planear.

La elegibilidad exige un grupo mínimo de 5% en entrenamiento. Se selecciona por silhouette de validación entre elegibles; prueba sirve para evaluar la selección congelada, sin cambiarla después de observar su resultado. Los grupos requieren interpretacion territorial y valoracion de su estabilidad; una mejor cifra aislada no demuestra utilidad operativa.

Responsable de revisar el análisis y la propuesta: Diego Hurtado.

## Estado de cierre

Las revisiones de las tres selecciones y su integración están completas. Marco ejecutó las reproducciones, conservó la calibración aprobada de P2 y verificó coincidencia de métricas, modelos y artefactos. Los tres modelos se registraron con alias `champion` y se cargaron correctamente en una ejecución independiente.

El cierre documental de reproducción y registro se integró mediante el PR #25, revisado por Diego Hurtado. La [interpretación de los grupos de P3](p3.md) quedó integrada mediante el PR #26, revisado por Marco, y conserva las gráficas originales y las limitaciones de separación y estabilidad.

Las [capturas de la interfaz](capturas_mlflow_marco.md) ya están preparadas y revisadas visualmente. Quedan su revisión por otro integrante y la incorporación al reporte consolidado. Los responsables, dependencias y archivos de comprobación están en el [cierre técnico](cierre_tecnico_marco.md).

La base historica se respaldo antes de agregar las corridas. Se conserva el intento de ingesta fallido por configuración inicial del entorno, seguido por la reconstruccion verificada. No se incluyen viajes, Parquet, bases SQLite, carpetas de MLflow ni modelos serializados en Git.
