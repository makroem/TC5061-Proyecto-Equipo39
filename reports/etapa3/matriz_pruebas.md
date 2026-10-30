# Matriz inicial de pruebas — Etapa 3

Inventario preparado por Marco sobre `main` `7aa3b639af13c9c5efb7c750a527f3a5cbc3868e`.
Las filas indican contratos que deben verificarse; los resultados ejecutados se registran
en `avance_marco.md`. La existencia de un archivo no demuestra por sí sola cobertura completa.

| Área / responsable | Función o contrato | Casos y archivos | Situación |
|---|---|---|---|
| Ingesta / Marco | `csv_options`, `column_name`, `clean_stations` | UTF-8/BOM/CP1252, separadores, acentos, columnas ausentes, IDs vacíos/repetidos, capacidad y coordenadas inválidas. `tests/test_ingesta_calidad.py` | Ampliado en esta rama |
| Ingesta / Marco | `clean_trips`, `unique_chunk` | Límites del periodo, fechas inválidas, duración cero/negativa, ausencia de estaciones, conservación de salidas, duplicados dentro/entre bloques. `test_data.py`, `test_ingesta_calidad.py` | Ampliado en esta rama |
| Descarga / Marco | `download_file` | Caché y SHA256, cliente HTTP, reintento, contenido vacío/HTML/distinto, conexión interrumpida y limpieza del archivo parcial. `test_download.py`, `test_ingesta_calidad.py` | Ampliado en esta rama |
| Versionado / Marco | `logical_hash`, `write_part`, `ingest` | Orden de filas, cambio de valores, Parquet y conteos, reconstrucción anual sintética, fuente modificada, manifiesto ausente o inconsistente. `test_data.py`, `test_ingesta_calidad.py` | Ampliado en esta rama |
| Calendario y partición / Stefania | `chronological_split`, `add_calendar_features`, agregación horaria | Pruebas previas en `test_features.py`, `test_split_isolation.py`; revisar límites, faltantes y aislamiento de información futura | Revisión y ampliación de Etapa 3 pendientes |
| P1 / Stefania | Baseline, codificación por estación, entrenamiento y predicción | `test_stage2_p1.py` y contratos previos; revisar entradas vacías, esquema y errores controlados | Aporte de Etapa 3 pendiente |
| P2 / Diego Martinez | Proxy, umbrales, probabilidades, sensibilidad y clase única | `test_p2_targets.py`, `test_p2_model.py`, `test_runtime_regressions.py`, `test_stage2_p2.py` | Aporte de Etapa 3 pendiente |
| P3 / Diego Hurtado | Perfiles, elegibilidad, escalado, grupos, métricas y artefactos | `test_p3.py`, `test_stage2_p3.py`; revisar perfiles degenerados, estaciones ausentes y límites de grupos | Aporte de Etapa 3 pendiente |
| Registro y controlador / Diego Martinez | Selección antes de test, linaje, firma, carga y alias temporal | `test_stage2_contract.py`, `test_stage2_project.py`, `test_stage2_registry.py`, `test_train.py` | Contratos previos disponibles; revisión de Etapa 3 pendiente |
| Calidad real / Diego Martinez y responsables de pregunta | Nulos, tipos, duplicados, integridad y drift | Motor `validation/data_checks.py`, política y pruebas negativas de comprobaciones obligatorias | Pendiente; no cubierto por el ejemplo sintético de compatibilidad |
| Seguridad / Marco | Exclusiones, análisis estático, dependencias e historial | Bandit, pip-audit, revisión de archivos y escaneo de secretos | Diagnóstico preliminar; repetir después de integrar |
| Integración / Marco | Reproducción completa desde clon limpio | Suite completa, datos preparados y política congelada | Depende de los PR técnicos del equipo |

No se fija un porcentaje de cobertura para declarar el trabajo excelente. La cobertura
ayuda a localizar funciones sin pruebas; debe acompañarse de casos normales, límites
y errores relevantes. Las pruebas sintéticas no certifican la calidad de los CSV reales.
