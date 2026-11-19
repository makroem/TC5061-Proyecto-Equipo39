# Seis verificaciones documentales de operación

Marco, 19 de noviembre de 2026. Respaldo de #76 sobre `7c49a81` y las fuentes incorporadas por #72. Esta revisión comprueba documentación y evidencia publicada; no representa una nueva ejecución local ni una revisión de Diego Martínez.

| Punto | Resultado documental | Evidencia | Observación |
|---|---|---|---|
| Comando único de inicio | Conforme | [README](../../README.md#etapa-6-microservicios-cicd-y-finops) y [Compose](../../docker-compose.yml) | `docker compose up --build -d --wait --wait-timeout 300`. Requiere Docker Linux y el paquete P1 verificado en `models/serving/p1/`. |
| Dirección de disponibilidad | Conforme | [README](../../README.md#etapa-6-microservicios-cicd-y-finops), [Compose](../../docker-compose.yml) y [comprobación de P1](../../references/etapa6/checks/smoke_p1.json) | `http://127.0.0.1:8006/ready`; el puerto habitual 8000 pertenece al ejemplo aislado de Etapa 4. |
| Petición y respuesta | Conforme | [Entrada](../../references/etapa4/examples/predict_request.json), [salida](../../references/etapa4/examples/predict_response.json) y [validador](../../mibici_equipo39/operations/smoke.py) | POST a `/predict`; P1 versión 1 devuelve 1.6764705882352942 para el ejemplo. La evidencia cubre lotes 1, 10 y 100, y vacío con 422. |
| Persistencia | Conforme | [Registro](../../references/etapa6/checks/persistence.json), [Compose](../../docker-compose.yml) y [revisión independiente](cierre_revision_20261119.md) | Volumen `tracking` propio; `docker compose down` lo conserva. No ejecutar `down -v` si se desea conservarlo. |
| Flujo automático | Conforme en el PR y en main | [Controles de #72](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/72/checks), [ejecución de integración](https://github.com/makroem/TC5061-Proyecto-Equipo39/actions/runs/44553281639) y [workflow](../../.github/workflows/etapa6.yml) | Pruebas Windows/Linux y construcción/despliegue correctos después de integrar. La prueba usa un modelo sintético identificado. |
| Correspondencia de gráficas | Conforme | [Generador](../../scripts/plot_load.py), [performance.csv](../../references/etapa6/mediciones_marco/performance.csv), [resources.csv](../../references/etapa6/mediciones_marco/resources.csv) y [u30_r1.json](../../references/etapa6/mediciones_marco/locust/u30_r1.json) | Las dos primeras gráficas resumen las tablas; la serie de Locust utiliza `history` de u30_r1. Sus ventanas móviles no equivalen al promedio de toda la corrida. |

Se corrigió la afirmación antigua del README que indicaba ausencia de mediciones de concurrencia. También se excluye `tests/operations` al reproducir el alcance histórico de Etapa 3, sin sumar sus pruebas al resultado de 284 aprobado el 7 de noviembre.

Diego Martínez puede revisar estos seis puntos y registrar sus observaciones bajo su propia autoría. El respaldo de Marco evita que la documentación técnica dependa de esa disponibilidad.
