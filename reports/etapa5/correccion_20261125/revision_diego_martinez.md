# Revisión del linaje y la conservación de métricas de la corrección estacional

Tarea #85. Revisó Diego Martinez el 27 de noviembre de 2026, sobre la rama
`fix/marco-drift-estacional-20261125` en `f5f645b` ([PR #86](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/86)).
Desde `a2f5122` la rama solo agrega las revisiones de Diego Hurtado (#92) y Stefania (#93), así que
lo comprobado aplica también a ese commit. Es una revisión de archivos publicados: no descargué el
paquete del modelo, no entrené y no repetí el ensayo A/B ni Evidently.

## Comprobaciones

| # | Comprobación | Resultado | Fuente |
|---|---|---|---|
| 1 | Linaje del modelo A | Conforme. Los tres archivos dicen `mibici-equipo39-p1-demanda`, versión 1, run `66414a8b45164d3a8f5b9f42e7cb387b` y paquete `dedce1eb…bd80`. `protocolo.json` fija la misma versión y run en `expected_a_version` y `expected_a_run`, y la huella del protocolo `ac586851…f596` coincide en los tres resúmenes. | [`resumen.json`](resumen.json), [`predicciones_manifiesto.json`](predicciones_manifiesto.json), [`model_manifest.json`](../../../references/etapa4/model_manifest.json), [`protocolo.json`](../../../references/etapa5/protocolo.json) |
| 2 | Cohorte y muestreo | Conforme. La cohorte de `data_manifest.json` tiene 369 estaciones únicas. Cada octubre tiene 274,536 filas, que son 369 estaciones por 31 días por 24 horas. Las medias de la tabla del informe usan toda la población (2,152,008, 274,536 y 274,536 filas) y coinciden con `populations` en `resumen.json`. Evidently usa 100,000 filas por conjunto con semilla 39 en las dos comparaciones, como fija el protocolo (`drift_sample_size`, `seed`) y aplica `seasonal.py`. | [`resumen.json`](resumen.json) (`seasonal_periods`, `populations`, `comparisons.*.sampling`), [`data_manifest.json`](../../../references/etapa5/data_manifest.json), [informe PDF](entrega/TC5061_Drift_ABTest_Equipo39.pdf), páginas 1 y 2 |
| 3 | Tabla A/B del informe | Conforme. PDF y DOCX muestran MAE 1.239267 y 1.208781, RMSE 2.440745 y 2.379533, p95 de 38.22 y 33.89 ms y mejora de 2.46%. Coinciden con `ab_resultados.json`, que conserva MAE A 1.2392674466412144 y B 1.2087805544696755. El intervalo [−0.032590, −0.027244] y los 1,000 remuestreos de bloques de 7 días también coinciden. El MAE actual de A en `resumen.json` es el mismo valor original. | [`ab_resultados.json`](../ab_resultados.json), [informe PDF](entrega/TC5061_Drift_ABTest_Equipo39.pdf), página 3, [DOCX](entrega/TC5061_Drift_ABTest_Equipo39.docx) |
| 4 | Entregas anteriores sin cambios | Conforme. Frente a `main` en `39fcd9a`, el diff solo agrega archivos y modifica `README.md`. No toca `reports/etapa5/` fuera de `correccion_20261125/`, ni `references/etapa4/`, ni los archivos previos de `references/etapa5/`. `ab_resultados.json`, `ab_metricas.csv`, `drift_variables.csv`, `protocolo.json` y `model_manifest.json` son idénticos byte a byte en la rama y en `main`. | `git diff --name-status 39fcd9a...f5f645b`, [`verificacion_tecnica.json`](verificacion_tecnica.json) |

## Observaciones

1. Las huellas de `original_sha256` en `verificacion_tecnica.json` corresponden a los archivos con
   saltos de línea CRLF de un checkout en Windows. En macOS o Linux, con LF, `shasum` da otro valor.
   Convertí los cinco archivos a CRLF y las cinco huellas coinciden, así que el contenido no cambió.
   Conviene anotarlo para quien repita la comprobación fuera de Windows.
2. El README de la rama resume la Etapa 5 y sustituye los párrafos del 11 y 16 de noviembre por
   enlaces a los antecedentes. Los archivos de esos resultados siguen sin cambios.
3. `predicciones_manifiesto.json` registra pyarrow 19.0.1 y `resumen.json` pyarrow 23.0.1. No es
   una discrepancia: son los dos entornos separados que describe la guía, uno para predecir y otro
   para Evidently.

No encontré discrepancias de linaje ni de métricas. Esta revisión no cambia datos, modelos,
protocolo, alias ni resultados.
