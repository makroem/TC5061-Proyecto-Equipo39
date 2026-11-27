# Cotejo de enlaces y evidencia de entrega

Tarea #90. Revisó Diego Martinez el 27 de noviembre de 2026, sobre `main` en `39fcd9a` y la rama
`feat/marco-etapa7-cierre` del [PR #91](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/91)
en `8635d5b`. Es independiente de la revisión de linaje de la tarea #85. No descargué modelos, no
entrené y no levanté servicios.

Los seis elementos están en `main`. El PR #91 no modifica ninguno; solo los enlaza desde
`docs/etapa7/README.md` y `references/etapa7/Indice_Entrega_Final_Equipo39.md`, que todavía son
propuesta.

## Elementos

| # | Elemento | Ruta en `main` | Enlace | Observación |
|---|---|---|---|---|
| 1 | MLproject | [`MLproject`](../../MLproject) | Abre en `main`. Los dos índices del PR #91 lo enlazan bien. | Sus 10 puntos de entrada llaman a módulos que existen en `mibici_equipo39/`, y `python_env.yaml` y `requirements.txt` también existen. No lo ejecuté porque requiere los datos. |
| 2 | Manifiesto de P1 | [`references/etapa4/model_manifest.json`](../../references/etapa4/model_manifest.json) | Abre en `main` y desde los índices y la Model Card del PR #91. | Nombre, versión 1, run `66414a8b…`, versión de datos, commit `288a592`, alias `champion` y firma coinciden con la versión A de [`references/etapa5/models.json`](../../references/etapa5/models.json). El alias actual del Registry no se puede consultar desde aquí. |
| 3 | `docker-compose.yml` | [`docker-compose.yml`](../../docker-compose.yml) | Abre en `main` y desde los dos índices del PR #91. | `docker compose config --quiet` sin errores. No cambió desde `19a0e0a`, donde lo ejecuté completo en la [revisión de Etapa 6](../etapa6/revision_verificaciones_diego_martinez.md). |
| 4 | Ejecución de CI | [`.github/workflows/etapa6.yml`](../../.github/workflows/etapa6.yml) | La [ejecución 45110141956](https://github.com/makroem/TC5061-Proyecto-Equipo39/actions/runs/45110141956) sobre `39fcd9a` terminó `success` en pruebas Windows, pruebas Linux y `build-deploy`. | Los índices del PR #91 enlazan el archivo del workflow, no una ejecución. En el PR #91, las ejecuciones 46018991653 (Etapa 6) y 46018991669 (integridad de Etapa 7) sobre `8635d5b` también terminaron `success`, pero son de la propuesta, no de `main`. |
| 5 | Gráfica de Locust | [`locust_serie_30_usuarios.png`](../../references/etapa6/mediciones_marco/locust_serie_30_usuarios.png) | Abre en `main` y se muestra en [`docs/etapa6/estado.md`](../etapa6/estado.md). | Muestra solicitudes por segundo y p95 del perfil de 30 usuarios, repetición 1. Ya la había regenerado desde `u30_r1.json` en la revisión de Etapa 6. Los índices del PR #91 enlazan `tests/load/locustfile.py`, no la gráfica. |
| 6 | Cálculo FinOps | [`finops.py`](../../mibici_equipo39/operations/finops.py), [`finops_sensitivity.csv`](../../references/etapa6/mediciones_marco/finops_sensitivity.csv) | Abren en `main`. El índice del PR #91 enlaza `estado.md` y `docs/etapa7/README.md` enlaza `finops.py`. | Recalculé las 81 filas con 1000 × tarifa / (predicciones por segundo × 730 × 3600 × uso) y todas coinciden. Las medianas a 24 USD dan la misma tabla de `estado.md`: de 0.011996 a 0.000141 USD por 1000 inferencias. |

## Sugerencias para el índice del PR #91

1. Enlazar la ejecución de CI de `main` sobre el commit final, además del archivo del workflow.
2. Enlazar la gráfica de Locust junto a `locustfile.py`, porque el script no muestra resultados.

No encontré enlaces rotos en los seis elementos. Esta revisión no cambia datos, modelos, mediciones ni
resultados.
