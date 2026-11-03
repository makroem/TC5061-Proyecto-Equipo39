# Reproducción y registro final de la Etapa 2

Actualización: 27 de octubre de 2026, America/Mexico_City. Responsable de ejecución: Marco.

Las selecciones revisadas de P1, P2 y P3 se reprodujeron mediante MLflow Projects y los tres modelos quedaron registrados como versión 1 con el alias `champion`. Una ejecución independiente cargó los tres modelos por nombre y alias, y comprobó que sus predicciones coincidieran con los ejemplos guardados. El cierre técnico no sustituye las capturas de la interfaz ni el reporte final de la entrega.

## Revisiones e integración

Stefania aprobó P1, Diego Martinez aprobó P2 y Diego Hurtado aprobó P3 en el [PR 22](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/22), integrado en `288a592aba240983c8d21c8128c16be4cbf0f2df`. Ese es el commit de las tres reproducciones, ejecutadas con el repositorio limpio.

El [PR 23](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/23) incorporó la sensibilidad de P2 y el tratamiento de métricas no evaluables. Marco lo revisó e integró después de comprobar 124 pruebas de la integración. La reproducción de P2 incluye esa implementación y conserva los umbrales aprobados: 0.65 para bicicletas y 0.70 para anclajes.

Marco revisó e integró el [PR 24](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/24), de Diego Hurtado, en `1e6e89b2de21d497936624f7065d7de42066fb53`. Ese cambio amplía la justificación de P3; modifica documentación y no altera el código de las reproducciones.

Diego Hurtado revisó e integró el [PR 25](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/25), de Marco, en `44f4dc73d2cfe1a72ae2e7eeb042dd4807df5c47`. Quedaron incorporadas las comprobaciones de reproducción, registro y carga por alias, junto con las dos gráficas originales de la búsqueda seleccionada de P3.

Marco contrastó la interpretación de Diego Hurtado con esas gráficas, los tamaños de los grupos, la comparación oficial y el linaje del modelo. El [PR 26](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/26) quedó aprobado e integrado en `6f7cbafcfa08c6545cf5b592d8de5133d01fb6e0`. La interpretación de los perfiles horarios y la distribución geográfica de P3 está terminada. Estos dos cambios son documentales y no representan nuevos entrenamientos.

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

## Reproducción y actualización del reporte

Este documento conserva el cierre técnico histórico del 27 de octubre de 2026. Para ejecutar el código actual usar la [guía sin entrada manual](reproduccion.md). El punto de entrada `reproduce` utiliza las selecciones aprobadas ya versionadas y obtiene automáticamente los identificadores nuevos.

El [reporte editable](ReporteParte2_MLflow_Equipo39.docx) y el [PDF corregido](TC5061_Reporte_MLFlow_Equipo39.pdf) incorporan las comparaciones y las capturas oficiales. La ampliación de [P1](p1.md) y [P2](p2.md) documenta costo y estabilidad con resultados comprobables. Las figuras del 28 de octubre se mantienen identificadas como evidencia histórica; una validación posterior en un almacén aislado no las sustituye.

La corrección corresponde a Marco y la revisión independiente a Diego Hurtado. La integración requiere su aprobación y el cumplimiento de las protecciones de main. No se atribuye esta revisión a los demás integrantes. El envío o la aceptación del reporte corregido por el docente se confirma por separado.

Las limitaciones de los modelos permanecen: P1 conserva el baseline, P2 tiene baja precisión y usa un proxy, y P3 presenta menor separación de prueba y menor estabilidad que su baseline. La guía documenta además el 404 observado en la descarga del catálogo el 2 de noviembre; no se declara resuelta la descarga desde cero.

## Archivos de evidencia

- [Capturas de la interfaz y pies de imagen](capturas_mlflow_marco.md).

- [Comparaciones y justificación de las búsquedas](busquedas_oficiales_marco.md).
- [Verificación de las reproducciones](verificacion_reproduccion_final_marco.json): métricas, comparación, configuración, firmas y evaluación.
- [Verificación del registro](verificacion_registry_final_marco.json): versiones, alias, descripciones, linaje y carga independiente.
- [Justificación e interpretación visual de P3](p3.md), incorporadas mediante los PR 24 y 26.

Estos archivos contienen resultados y metadatos. No incluyen viajes, bases de MLflow, modelos serializados ni credenciales.
