# Reproducción y registro final de la Etapa 2

Actualización: 27 de octubre de 2026, America/Mexico_City. Responsable de ejecución: Marco.

Las selecciones revisadas de P1, P2 y P3 se reprodujeron mediante MLflow Projects y los tres modelos quedaron registrados como versión 1 con el alias `champion`. Una ejecución independiente cargó los tres modelos por nombre y alias, y comprobó que sus predicciones coincidieran con los ejemplos guardados. El cierre técnico no sustituye las capturas de la interfaz ni el reporte final de la entrega.

## Revisiones e integración

Stefania aprobó P1, Diego Martinez aprobó P2 y Diego Hurtado aprobó P3 en el [PR 22](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/22), integrado en `288a592aba240983c8d21c8128c16be4cbf0f2df`. Ese es el commit de las tres reproducciones, ejecutadas con el repositorio limpio.

El [PR 23](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/23) incorporó la sensibilidad de P2 y el tratamiento de métricas no evaluables. Marco lo revisó e integró después de comprobar 124 pruebas de la integración. La reproducción de P2 incluye esa implementación y conserva los umbrales aprobados: 0.65 para bicicletas y 0.70 para anclajes.

Marco revisó e integró el [PR 24](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/24), de Diego Hurtado, en `1e6e89b2de21d497936624f7065d7de42066fb53`. Ese cambio amplía la justificación de P3; modifica documentación y no altera el código de las reproducciones.

## Resultados reproducidos

La versión de los datos y la partición coinciden con las búsquedas oficiales. Se conservaron las selecciones aprobadas y no se repitió la calibración de P2 ni se seleccionó con test.

| Pregunta | Selección | Métrica | Validación | Prueba |
|---|---|---|---:|---:|
| P1 | Baseline de medias históricas | MAE | 0.888775 | 0.916381 |
| P2 | Logística, C=0.1 | Promedio de F1 positivos de ambos riesgos | 0.042360 | 0.052181 |
| P3 | GMM, 3 componentes | Silhouette | 0.026594 | 0.051373 |

La comparación automática entre búsqueda y reproducción comprobó MAE/RMSE de P1; F1, precisión y recall de ambos riesgos de P2; y silhouette de P3. Todas las comparaciones cumplieron la tolerancia relativa de 1e-8 y absoluta de 1e-10. Los tiempos y tamaños se conservan como medidas de cada ejecución, sin exigir igualdad de tiempos entre equipos o sesiones.

También se verificaron las carpetas `model/`, `data/`, `config/`, `evaluation/` y `plots/`; la firma, el ejemplo de entrada y la predicción al recargar cada modelo; los manifiestos; y la sensibilidad de P2 para ocupaciones iniciales de 25% y 75% en validación y prueba.

| Pregunta | Corrida padre de reproducción | Corrida del modelo |
|---|---|---|
| P1 | `7776756ca1564b959caa2545321a1a3c` | `66414a8b45164d3a8f5b9f42e7cb387b` |
| P2 | `20b5b70882ac4fc2aeec62fa48e67731` | `73804085f3944b54ac2f99542eec38be` |
| P3 | `4c09c894d6c048ae8218ba738227bd87` | `fb847f28e5484ff885e8ef9b44afb2d7` |

Versión de datos: `e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7`.

Partición: `ab6301f96f083217512343b4f800bc5ddea51b666492ef05b34da85591cc9bdd`, versión 3, `chronological_holdout`, semilla 39.

## Model Registry y ciclo de vida

El alias `champion` identifica la versión elegida para producción académica. Permite conservar el nombre de consumo mientras se asigna una versión distinta después de una futura evaluación. El código comprueba la corrida, el linaje y la carga de la versión antes de asignar el alias. Este estado no representa un servicio desplegado ni demuestra utilidad operativa.

| Pregunta | Nombre registrado | Versión | Alias | Carga por nombre |
|---|---|---:|---|---|
| P1 | `mibici-equipo39-p1-demanda` | 1 | `champion` | Correcta |
| P2 | `mibici-equipo39-p2-riesgo` | 1 | `champion` | Correcta |
| P3 | `mibici-equipo39-p3-grupos` | 1 | `champion` | Correcta |

La verificación independiente se ejecutó mediante `mlflow run . -e verify_registry`, corrida `77d302adcd404ab7aa8be53c4eeb2896`, con estado `FINISHED`. Cada versión conserva descripción, corrida de origen, commit, versión de datos y partición. El registro reside en el servidor local del equipo; las bases y los modelos no se publican en GitHub.

## Comandos de reproducción

Desde un clon limpio, seguir primero la instalación y el inicio del servidor descritos en el [README](../../README.md) y el [contrato de infraestructura](../../references/etapa2/contrato_infraestructura.md). Para reproducir exactamente este corte, usar el commit `288a592aba240983c8d21c8128c16be4cbf0f2df`. En PowerShell, con el entorno de dependencias fijas activo y el servidor en ejecución:

```powershell
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
mlflow run . -e ingest --env-manager local --experiment-name mibici-equipo39
foreach ($pregunta in @("p1", "p2", "p3")) {
    mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=$pregunta -P model=selected -P mode=reproduce -P member=Marco
    if ($LASTEXITCODE -ne 0) { throw "Revisar la ejecución de $pregunta antes de continuar." }
}
```

Para registrar una reproducción nueva, tomar el identificador de su corrida hija del resumen generado y utilizar el punto de entrada `registry`. Los identificadores de esta evidencia pertenecen al servidor donde se ejecutó el cierre; un servidor nuevo genera otros.

```powershell
$pregunta = "p1"
$corrida = Read-Host "Identificador de la corrida hija reproducida para p1"
mlflow run . -e registry --env-manager local --experiment-name mibici-equipo39 -P question=$pregunta -P source_run_id=$corrida
```

Repetir el registro para P2 y P3 con sus identificadores. Una vez registrados los tres:

```powershell
mlflow run . -e verify_registry --env-manager local --experiment-name mibici-equipo39
```

## Límites y pendientes de entrega

P1 conserva el baseline porque los tres candidatos tuvieron mayor MAE de validación. P2 mejora F1 frente al baseline, pero su precisión de prueba es baja y las etiquetas representan un riesgo aproximado sin inventario observado. P3 cumple la elegibilidad de entrenamiento y gana en silhouette de validación, aunque tiene menor estabilidad ARI y menor silhouette de prueba que el baseline. Estas limitaciones permanecen en la interpretación; el registro no las corrige.

| Pendiente | Responsable | Qué necesita |
|---|---|---|
| Revisar este cierre documental antes de integrarlo | Otro integrante con permisos de escritura | Contrastar las evidencias y aprobar el PR de Marco |
| Interpretar perfiles horarios y distribución de los grupos de P3 | Diego Hurtado | Inspeccionar `plots/perfiles_grupos.png`, `plots/ubicacion_grupos.png` y asignaciones del modelo seleccionado |
| Completar capturas de comparaciones con nested runs, artefactos y tres modelos con linaje y alias | Marco, en coordinación con Diego Hurtado | Acceso visual al servidor local y capturas reales legibles |
| Consolidar Word y PDF de la entrega | Diego Hurtado, con las aportaciones del equipo | Resultados, interpretación de P3, capturas y referencias APA 7 |
| Confirmar el envío en Canvas | Integrante designado por el equipo | PDF final y comprobante de entrega |

El Word previo contiene un corte anterior y debe actualizarse antes de presentarlo como reporte final. La evidencia técnica disponible no acredita el envío en Canvas.

## Archivos de evidencia

- [Comparaciones y justificación de las búsquedas](busquedas_oficiales_marco.md).
- [Verificación de las reproducciones](verificacion_reproduccion_final_marco.json): métricas, comparación, configuración, firmas y evaluación.
- [Verificación del registro](verificacion_registry_final_marco.json): versiones, alias, descripciones, linaje y carga independiente.
- [Justificación de P3](p3.md), incorporada mediante el PR 24.

Estos archivos contienen resultados y metadatos. No incluyen viajes, bases de MLflow, modelos serializados ni credenciales.
