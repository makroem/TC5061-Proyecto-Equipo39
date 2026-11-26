# Entrega final de MiBici

**Preparación iniciada el 25 de noviembre de 2026.** Marco coordina; Diego Hurtado revisa. El [manual editable](../../references/etapa7/Manual_Etapa7_Entrega_Final_Equipo39.docx) contiene actividades por persona, comandos, dependencias, criterios de cierre y guion de 4 minutos 30 segundos. Esta página no declara completada la entrega final.

## Estado y responsables

| Trabajo | Responsable | Estado y dependencia |
|---|---|---|
| Manual, índice, Model Card e integridad de originales | Marco, [#87](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/87) | Preparados en `feat/marco-etapa7-cierre`; pendientes de revisión e integración |
| Corrección estacional de drift | Diego Hurtado revisa; Marco integra | [#86](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/86) abierto al corte; depende de [#83](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/83) |
| Ciclo nuevo de entrenamiento y promoción aceptada | Marco ejecuta; Diego Hurtado valida | [Protocolo preparado](continuous_training.md); implementación, datos de evaluación y ejecución pendientes |
| Reproducción y revisión independiente final | Diego Hurtado, [#88](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/88) | Depende del cambio y de los resultados concretos de Marco |
| Revisión de uso y límites de la Model Card | Stefania, [#89](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/89) | Breve y no bloqueante; respaldo de Marco y validación de Diego Hurtado |
| Cotejo de seis enlaces y evidencia | Diego Martínez, [#90](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/90) | Breve y no bloqueante; respaldo de Marco o Diego Hurtado |
| Presentación editable y video de 2 a 5 minutos | Marco coordina; diálogos del equipo | Guion en el manual; archivos finales y grabación real pendientes |

Las tareas pequeñas no impiden avanzar con la implementación. Su respaldo no acredita una contribución de quien no la realizó. La revisión independiente de una promoción y la demostración real siguen siendo condiciones de cierre.

## Evidencias por criterio

| Criterio | Rutas existentes | Comprobación final |
|---|---|---|
| Estructura y experimentación, 20% | [MLproject](../../MLproject), [entorno](../../python_env.yaml), [features](../../mibici_equipo39/features.py), [reporte MLflow](../../reports/etapa2/reporte_corregido.md) | Comando reproducible y corrida vinculada a código y datos |
| Modelo y Registry, 15% | [Manifiesto P1](../../references/etapa4/model_manifest.json), [versiones A/B](../../references/etapa5/models.json), [Model Card](../../MODEL_CARD.md) | Consultar versión, run, firma y alias en Registry; justificar aceptación |
| Despliegue y operación, 25% | [Compose](../../docker-compose.yml), [API](../../mibici_equipo39/serving), [workflow](../../.github/workflows/etapa6.yml), [Locust](../../tests/load/locustfile.py), [carga y costos](../etapa6/estado.md) | Petición HTTP real y CI exitoso sobre el cambio final; conservar limitaciones de latencia |
| Monitoreo, gobernanza y FinOps, 20% | [A/B original](../../reports/etapa5/analisis_ab.md), [monitoreo](../../mibici_equipo39/monitoring), [FinOps](../../mibici_equipo39/operations/finops.py), [Model Card](../../MODEL_CARD.md) | Integrar corrección estacional aprobada y demostrar ciclo nuevo según el protocolo |
| Presentación y demo, 20% | [Manual y guion](../../references/etapa7/Manual_Etapa7_Entrega_Final_Equipo39.docx) | Publicar editable y video de 2 a 5 minutos con demostración funcional |

La versión 1 se conserva temporalmente. B mejora el MAE 2.46%, pero no alcanza los criterios de promoción de Etapa 5. No se presenta B como candidata aprobada ni el diseño del ciclo como una ejecución terminada.

## Comprobación breve

Desde la raíz del clon:

```powershell
python -B -m scripts.check_final_evidence
python -m unittest discover -s tests/final -v
```

El [inventario](../../references/etapa7/baseline_sha256.json) protege **301 archivos históricos** de `reports/` y `references/` sobre `39fcd9a`. Registra la huella del contenido almacenado en Git y, cuando difiere por la conversión de saltos de línea, la de la copia original de Windows. No normaliza ni reescribe mediciones. La verificación local inicial aprobó; las cuatro pruebas del verificador también. El [workflow de integridad](../../.github/workflows/etapa7.yml) repite esas comprobaciones en GitHub. No evalúa la calidad estadística del modelo ni sustituye los controles de API, monitoreo y despliegue.

Para la demo de la versión operativa, con Docker Linux y P1 original verificado en `models/serving/p1/`:

```powershell
docker compose up --build -d --wait --wait-timeout 300
Invoke-RestMethod http://127.0.0.1:8006/ready
$body = Get-Content references/etapa4/examples/predict_request.json -Raw
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8006/predict -ContentType 'application/json' -Body $body
```

El README conserva la preparación del paquete y del entorno. Mostrar la respuesta producida por el servicio, no el ejemplo estático. La fixture de CI tiene otra identidad y no sustituye P1. Cambiar el alias del Registry tampoco cambia por sí solo el paquete fijado en el contenedor.

## Cierre pendiente

Después de ejecutar el ciclo, revisar e integrar los cambios, completar `docs/etapa7/cierre.md` con commit de main, enlace al pipeline exitoso, identidad servida, run del candidato, aprobación y alias verificado, enlaces al editable/video y duración. Conservar capturas auténticas y huellas de todos los resultados nuevos. La etapa no se cierra por la sola existencia de esta lista.
