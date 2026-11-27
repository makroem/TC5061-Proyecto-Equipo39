# Model Card de P1 MiBici Equipo 39

Fecha de corte: 25 de noviembre de 2026. Responsable de mantenimiento: Marco. Revisión independiente asignada a Diego Hurtado en la [tarea #88](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/88). Documento inicial de la entrega final; no acredita una nueva promoción.

## Uso y alcance

El servicio estima viajes observados que comienzan en una estación durante una hora. Apoya la planeación de redistribución de bicicletas; sus resultados requieren interpretación operativa. No estima directamente demanda insatisfecha, disponibilidad de bicicletas, ingresos ni comportamiento individual. No debe utilizarse para decisiones sobre personas ni extrapolarse a estaciones sin historia comprobada.

La versión servida documentada es **1** de `mibici-equipo39-p1-demanda`, con alias histórico `champion`. Es el modelo operativo conservado bajo los criterios de aceptación del equipo; no es el de menor error global entre A y B. El alias debe consultarse nuevamente en el Registry antes de la entrega. No existe evidencia de un servicio público permanente: la API y Compose se validaron localmente.

## Modelo y linaje

| Elemento | Valor verificable |
|---|---|
| A versión 1 | Run `66414a8b45164d3a8f5b9f42e7cb387b` |
| Código de entrenamiento A | `288a592aba240983c8d21c8128c16be4cbf0f2df` |
| Versión de datos A | `e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7` |
| Huella del paquete A | `dedce1eb08bda971a42fba311224c88e56f75cd2789dbb391e9445951931bd80` |
| B versión 2 | Run `741ed805a55a49b3bb0bb95a4682b1f2`, candidata sin promover |
| Familia | Media por estación, día de semana y hora; respaldo por estación y hora y media global |
| Entrenamiento A | Octubre de 2025 a mayo de 2026 |
| Entrenamiento B | Octubre de 2025 a septiembre de 2026, 3,232,440 filas |
| Evaluación A/B | Octubre de 2026, 274,536 claves estación-hora de 369 estaciones |

Fuentes: [manifiesto del paquete](references/etapa4/model_manifest.json), [versiones](references/etapa5/models.json), [datos y huellas](references/etapa5/data_manifest.json) y [análisis A/B](reports/etapa5/analisis_ab.md). Los artefactos privados del modelo se recuperan del Registry o del paquete autorizado; el catálogo CSV de estaciones no es el modelo.

## Entradas y salida

La firma contiene `station_id`, `hour_of_day`, `day_of_week`, `month`, `is_weekend`, `hour_sin`, `hour_cos`, `month_sin` y `month_cos`. La API acepta de 1 a 100 filas; valida tipos, rangos y coherencia de calendario. Devuelve `predicted_trips`, nombre, versión y huella del paquete. La [especificación del contrato](references/etapa4/contrato_api.md) y el [ejemplo de petición](references/etapa4/examples/predict_request.json) son la referencia de implementación. La presencia de nueve campos en la firma no implica que la media estacional utilice todos para ajustar sus estimaciones; en particular, no adapta directamente el nivel de demanda al mes.

## Resultados y selección

| Medida sobre el mismo mes | A | B |
|---|---:|---:|
| MAE en viajes por estación-hora | 1.239267 | 1.208781 |
| RMSE en viajes por estación-hora | 2.440745 | 2.379533 |
| p95 en ms por lote local de 1000 filas | 38.22 | 33.89 |

B mejora el MAE 2.46%, por debajo del mínimo predefinido de 5%, y presenta incumplimientos del criterio relativo por segmentos. No se promueve. El intervalo exploratorio pareado del cambio de MAE es [-0.032590, -0.027244], calculado con bloques de siete días. Un solo mes y segmentos con demanda casi nula limitan la interpretación; esto no equivale a un experimento aleatorio en producción. La latencia anterior excluye HTTP y carga inicial.

La [corrección estacional propuesta en el PR #86](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/86), aún pendiente de integración al corte de esta ficha, compara octubre de 2026 con octubre de 2025 en las mismas estaciones: demanda media de 1.5301 a 2.1116 viajes por estación-hora, aumento de **38.00%**. La comparación contra ocho meses arroja 58.31%, pero mezcla temporadas. El objetivo conserva drift; las nueve entradas no muestran drift en la comparación estacional. A subestima **36.83% del total observado**. Una predicción estable no demuestra que el modelo siga siendo adecuado. Estas cifras describen un análisis propuesto con evidencia conservada, no una promoción aprobada.

## Limitaciones y riesgos

Los viajes observados dependen de bicicletas disponibles, horarios, cierres y demanda. El aumento no demuestra por sí solo una causa ni un cambio causal en la relación entre variables. Octubre de 2025 pertenece al entrenamiento de A: su error no constituye una evaluación independiente. La cohorte de estaciones restringe cobertura; un valor cero puede corresponder a una estación sin operación o sin registros, no necesariamente a ausencia de necesidad. No se utilizan atributos personales en la API. Los datos publicados de evidencia deben conservar únicamente agregados necesarios, sin credenciales ni registros identificables.

La operación local presentó incumplimientos de latencia con 10 y 30 usuarios; se conservan los resultados en [Etapa 6](docs/etapa6/estado.md). El costo por inferencia es una estimación con tarifa histórica, capacidad observada y escenarios de utilización; no es una factura ni una medición en nube. No se declara cumplimiento de un SLA público.

## Monitoreo y mantenimiento

Marco mantiene los datos, el código y la ficha; Diego Hurtado revisa la aceptación del candidato y la reversión. Stefania revisa claridad y limitaciones, y Diego Martínez contrasta enlaces y evidencias. El respaldo técnico de Marco o Diego Hurtado no atribuye participación a quien no ejecutó la tarea.

Antes de reentrenar, confirmar calidad, misma temporada, cohorte y drift de objetivo y predicción. Separar entrenamiento y evaluación temporal; registrar sus huellas, código, parámetros, firma y resultados. El [protocolo de cierre](docs/etapa7/continuous_training.md) define la ejecución aún pendiente. Mantener los umbrales acordados y la revisión independiente. Si falla un criterio, conservar el modelo vigente y documentar el rechazo. Si se aprueba otro modelo, registrar alias anterior y nuevo, generar su manifiesto y comprobar el contenedor con la nueva versión. Cambiar un alias no actualiza la API fijada por versión. Conservar la imagen, el paquete y el manifiesto previos para la reversión.
