# Revisión de la ficha y el linaje A/B de P1

Tarea #63. Revisó Diego Martinez el 14 de noviembre de 2026, sobre `main` en `21723ad`, que ya
integra los resultados de la rama `feat/marco-etapa5-monitoreo` (PR #64). Es una revisión de
archivos publicados: no se entrenó, no se abrió el servidor de MLflow y no se aprueba ninguna
promoción.

## Verificaciones

| # | Verificación | Resultado | Fuente |
|---|---|---|---|
| 1 | Nombre común del modelo | Comprobado. A y B son `mibici-equipo39-p1-demanda`. | `models.json` (`model_name` y las dos URI), `protocolo.json`, captura 04. |
| 2 | Versiones numéricas distintas | Comprobado. A es la versión 1 y B la versión 2. | `models.json`, `entrenamiento_b.json`, `ab_resultados.json`, captura 04. |
| 3 | Run de origen de cada versión | Comprobado. A: `66414a8b45164d3a8f5b9f42e7cb387b`. B: `741ed805a55a49b3bb0bb95a4682b1f2`. | `models.json`; A también en `references/etapa4/model_manifest.json`; B en `entrenamiento_b.json` y `cierre_corrida_b.json`; las dos en las etiquetas de la evaluación (captura 08). |
| 4 | Entrenamiento y evaluación sin solapamiento | Comprobado. A: 1 oct 2025 a 31 may 2026. B: 1 oct 2025 a 30 sep 2026. Evaluación: 1 a 31 oct 2026. | `protocolo.json` (límites superiores exclusivos), `datos_resumen.json` (primera y última hora de cada conjunto), `references/split_manifest.json` para la partición de A. |
| 5 | Huella del conjunto actual común a A/B | Comprobado. `eecb9aa8…c082`, 274,536 filas evaluadas con los dos modelos. | `data_manifest.json` y `ab_resultados.json` (`current_sha256`, `rows_both_models`), `compatibilidad_modelos.json`. |
| 6 | Alias `champion` conservado | Comprobado en lo publicado. `champion` sigue en la versión 1 y B no tiene alias. El estado actual del servidor no es verificable desde aquí. | `models.json` (`alias_at_freeze`), `decision.json` (`champion_unchanged`), `cierre_corrida_b.json`, captura 04 del 12 de noviembre. |

## Detalle

- **Punto 4.** La referencia de drift son las filas de entrenamiento de A: 2,152,008 filas y 243
  días, igual que el train de la partición cronológica de Etapa 2. B agrega los meses que antes eran
  validación y prueba, como lo indica el protocolo. Octubre de 2026 no está en el entrenamiento de
  ninguno de los dos. No pude recalcularlo desde los Parquet porque `data/monitoring/` no se publica
  en Git; me basé en los resúmenes.
- **Punto 5.** Tampoco recalculé la huella del Parquet actual, por la misma razón. Sí coincide en
  todos los archivos donde aparece, igual que la huella de entrenamiento de B (`fb6af296…5b31`).
- **Punto 6.** Diego Hurtado valida el alias en el servidor, según la tarea.

## Comprobaciones adicionales

- La huella SHA-256 de `references/etapa5/protocolo.json` coincide con `protocol_sha256` en
  `models.json`, `data_manifest.json`, `ab_resultados.json` y la etiqueta de la versión 2.
- Los commits de entrenamiento coinciden con las etiquetas del Registry: A `288a592`, B `23d7618`.
- Las nueve capturas de `reports/etapa5/capturas/` coinciden con las huellas de su `manifest.json`.

No encontré discrepancias. Esta revisión no cambia datos, modelos, protocolo, alias ni resultados.
