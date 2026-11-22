# Cierre y archivos de Marco en la Etapa 6

Corte: 22 de noviembre de 2026, hora de Ciudad de México. Revisión sobre `19a0e0ad2956de391c13aac77d8b07b135998787`.

La implementación, el análisis y el Word final de Marco están integrados mediante los PR #72, #77 y #78. La tarea #73 está cerrada. Este cambio añade el PDF del Word aprobado y actualiza el seguimiento; su publicación en main requiere la revisión habitual.

## Actividades comprobadas

| Actividad | Resultado y evidencia |
|---|---|
| Orquestación | API y tracking con un comando, red, volumen, variables, salud y recursos limitados. |
| CI/CD | [Main exitoso](https://github.com/makroem/TC5061-Proyecto-Equipo39/actions/runs/45046142850), 108 pruebas en cada sistema operativo, construcción y despliegue temporal. |
| Carga | Nueve ejecuciones de P1, 13,001 solicitudes, 36,176 predicciones útiles, cero fallos. Los perfiles de 10 y 30 usuarios incumplen la latencia objetivo. |
| Recursos | CPU y memoria muestreadas durante los ensayos; tablas y gráficas conservadas. |
| FinOps | 81 escenarios recalculados, costo por inferencia útil y recomendaciones con limitaciones explícitas. |
| Informe | Word final aprobado mediante #78. PDF de nueve páginas: cuatro principales y cinco de anexos; capturas y gráficas conservadas. |
| Colaboración | Marco implementó y documentó; Diego Hurtado aprobó #72, #77 y #78. Marco aprobó e integró la aportación de Diego Martínez mediante #80 y cerró #76. La aportación de Stefania (#79) sigue pendiente de revisión. |

## Archivos comprobados en main

Cada ruta siguiente existe en el commit de corte. Los archivos heredados de API y dependencias se reutilizan; esta lista no los atribuye como trabajo nuevo de esta etapa.

| Función | Ruta en GitHub |
|---|---|
| Automatización | [.github/workflows/etapa6.yml](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/.github/workflows/etapa6.yml) |
| Instrucciones de operación | [README.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/README.md) |
| Orquestación y dependencias | [deploy/Containerfile.api](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/deploy/Containerfile.api) |
| Orquestación y dependencias | [deploy/Containerfile.mlflow](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/deploy/Containerfile.mlflow) |
| Orquestación y dependencias | [docker-compose.yml](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docker-compose.yml) |
| Seguimiento e interpretación | [docs/etapa6/cierre_revision_20261119.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docs/etapa6/cierre_revision_20261119.md) |
| Seguimiento e interpretación | [docs/etapa6/estado.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docs/etapa6/estado.md) |
| Seguimiento e interpretación | [docs/etapa6/interpretacion_carga.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docs/etapa6/interpretacion_carga.md) |
| Seguimiento e interpretación | [docs/etapa6/seguridad_operacion.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docs/etapa6/seguridad_operacion.md) |
| Seguimiento e interpretación | [docs/etapa6/verificacion_documental.md](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/docs/etapa6/verificacion_documental.md) |
| Comprobación y cálculo | [mibici_equipo39/operations/__init__.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/__init__.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/finops.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/finops.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/http_client.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/http_client.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/log_load.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/log_load.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/payload.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/payload.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/smoke.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/smoke.py) |
| Comprobación y cálculo | [mibici_equipo39/operations/tracking_check.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/mibici_equipo39/operations/tracking_check.py) |
| Informes y manual | [references/etapa6/Manual_Etapa6_Microservicios_CICD_FinOps_Equipo39.docx](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/Manual_Etapa6_Microservicios_CICD_FinOps_Equipo39.docx) |
| Informes y manual | [references/etapa6/TC5061_Microservicios_FinOps_Equipo39.docx](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/TC5061_Microservicios_FinOps_Equipo39.docx) |
| Informes y manual | [references/etapa6/TC5061_Operacion_FinOps_Equipo39_Actualizado.docx](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/TC5061_Operacion_FinOps_Equipo39_Actualizado.docx) |
| Informes y manual | [references/etapa6/TC5061_Operacion_FinOps_Equipo39_Final.docx](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/TC5061_Operacion_FinOps_Equipo39_Final.docx) |
| Comprobaciones | [references/etapa6/checks/bandit.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/bandit.json) |
| Comprobaciones | [references/etapa6/checks/export_check.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/export_check.json) |
| Comprobaciones | [references/etapa6/checks/persistence.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/persistence.json) |
| Comprobaciones | [references/etapa6/checks/reporte_revision.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/reporte_revision.json) |
| Comprobaciones | [references/etapa6/checks/revision_independiente.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/revision_independiente.json) |
| Comprobaciones | [references/etapa6/checks/smoke_p1.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/smoke_p1.json) |
| Comprobaciones | [references/etapa6/checks/unit_tests.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/checks/unit_tests.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/finops_sensitivity.csv](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/finops_sensitivity.csv) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u01_r1.html](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u01_r1.html) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u01_r1.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u01_r1.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u01_r2.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u01_r2.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u01_r3.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u01_r3.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u10_r1.html](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u10_r1.html) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u10_r1.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u10_r1.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u10_r2.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u10_r2.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u10_r3.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u10_r3.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u30_r1.html](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u30_r1.html) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u30_r1.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u30_r1.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u30_r2.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u30_r2.json) |
| Resultados de Locust | [references/etapa6/mediciones_marco/locust/u30_r3.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust/u30_r3.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/locust_serie_30_usuarios.png](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/locust_serie_30_usuarios.png) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/performance.csv](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/performance.csv) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/protocol.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/protocol.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/recursos.png](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/recursos.png) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/rendimiento_latencia.png](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/rendimiento_latencia.png) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/resource_series.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/resource_series.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/resources.csv](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/resources.csv) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/source_sha256.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/source_sha256.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/summary.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/summary.json) |
| Mediciones gráficas y costo | [references/etapa6/mediciones_marco/tracking_runs.json](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/references/etapa6/mediciones_marco/tracking_runs.json) |
| Orquestación y dependencias | [requirements-api-dev.txt](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/requirements-api-dev.txt) |
| Orquestación y dependencias | [requirements-api.txt](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/requirements-api.txt) |
| Ejecución y consolidación | [scripts/create_ci_model.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/scripts/create_ci_model.py) |
| Ejecución y consolidación | [scripts/plot_load.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/scripts/plot_load.py) |
| Ejecución y consolidación | [scripts/run_load.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/scripts/run_load.py) |
| Ejecución y consolidación | [scripts/summarize_load.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/scripts/summarize_load.py) |
| Escenarios y pruebas | [tests/load/locustfile.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/tests/load/locustfile.py) |
| Escenarios y pruebas | [tests/operations/test_finops.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/tests/operations/test_finops.py) |
| Escenarios y pruebas | [tests/operations/test_http_client.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/tests/operations/test_http_client.py) |
| Escenarios y pruebas | [tests/operations/test_payload.py](https://github.com/makroem/TC5061-Proyecto-Equipo39/blob/main/tests/operations/test_payload.py) |

## Archivos añadidos por este cierre

- [PDF para entrega](../../references/etapa6/TC5061_Operacion_FinOps_Equipo39.pdf), exportado del Word aprobado sin reemplazarlo.
- [Verificación de integridad y resultados](../../references/etapa6/checks/entrega_marco_20261122.json).
- Este inventario.

Estos archivos se preparan en la rama `docs/marco-cierre-entrega-etapa6-20261122`; no se consideran integrados mientras el nuevo PR permanezca abierto.

## Dependencias y límites

- Diego Hurtado debe aportar los archivos originales de su ensayo, si los conserva, en #74. Marco no puede reconstruirlos ni atribuirse esa ejecución. Su ausencia no bloquea el cierre documental ya aprobado.
- PR #79: aportación de Stefania pendiente de revisión; una mejor relación que el perfil de 30 usuarios no convierte el perfil de 10 en cumplimiento del objetivo.
- PR #80: [aprobado por Marco](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/80#pullrequestreview-6014433070) sobre `c355593` e integrado mediante `4c37247` el 22 de noviembre a las 14:42, hora de Ciudad de México; #76 quedó cerrada. La [revisión individual de Diego Martínez](revision_verificaciones_diego_martinez.md) ya está en main y se conserva como aportación de su autor.
- La distribución histórica de aportaciones no es equilibrada. Las revisiones y nuevas contribuciones cuentan como tales; no se modifican autorías ni se promete una calificación.
- El despliegue de Actions es temporal y usa una fixture; no es producción ni prueba de capacidad con P1.
- La entrega en Canvas no se ha ejecutado en esta revisión.
