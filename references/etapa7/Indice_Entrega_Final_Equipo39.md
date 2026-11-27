# Índice de evidencias técnicas de la entrega final

| Elemento | Evidencia | Verificación |
|---|---|---|
| Presentación | [TC5061 Proyecto Final Equipo 39](TC5061_Proyecto_Final_Equipo39.pdf) | Seis diapositivas sobre el problema, la solución y las decisiones de operación. |
| Estructura y experimentación | [MLflow Project](../../MLproject) · [Código del proyecto](../../mibici_equipo39/) | Proyecto, preparación de variables y trazabilidad del entrenamiento. |
| Modelo P1 | [Manifiesto](../etapa4/model_manifest.json) · [Registro de versiones A/B](../etapa5/models.json) · [Ficha del modelo](../../MODEL_CARD.md) | P1 v1. Coinciden nombre, versión, corrida, datos, commit y firma entre el manifiesto y el registro A/B. |
| Despliegue y operación | [Compose](../../docker-compose.yml) · [Pipeline](../../.github/workflows/etapa6.yml) · [Prueba de carga](../../tests/load/locustfile.py) | Contenerización, comprobaciones automatizadas y escenario de prueba. |
| Monitoreo y costo | [Resultados A/B](../../reports/etapa5/analisis_ab.md) · [Corrección estacional propuesta](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/86) · [Operación y FinOps](../../docs/etapa6/estado.md) | Las cifras estacionales de la presentación corresponden a la corrección del PR #86. |
| Conservación de resultados | [Inventario histórico SHA-256](baseline_sha256.json) | Evidencias históricas verificadas sin reescribir archivos. |

## Linaje de P1

- Modelo: `mibici-equipo39-p1-demanda`, versión `1`.
- Corrida de origen: `66414a8b45164d3a8f5b9f42e7cb387b`.
- Commit de entrenamiento: `288a592aba240983c8d21c8128c16be4cbf0f2df`.
- Versión de datos: `e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7`.
- Huella del paquete: `dedce1eb08bda971a42fba311224c88e56f75cd2789dbb391e9445951931bd80`.
- Se cotejaron los 22 archivos del paquete contra el manifiesto. La respuesta guardada de la API coincide en nombre, versión y huella.
- `champion` es el alias documentado en el manifiesto. Esta verificación usa el paquete local y el registro A/B guardado.
