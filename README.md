# Proyecto MiBici Equipo 39

## Etapa 3: pruebas, validación y seguridad

La Etapa 3 del proyecto MiBici Equipo 39 está orientada a fortalecer la calidad del software, ampliar las pruebas automatizadas, comprobar la integridad de los datos y documentar los hallazgos de seguridad.

Las contribuciones técnicas de los cuatro integrantes ya fueron revisadas e integradas en `main`. La política de calidad está congelada. La [verificación integrada del 1 de noviembre](reports/etapa3/cierre_integrado_marco_20261101.md) documenta 238 pruebas aprobadas y la corrida final de datos: 100 PASS, 3 WARN, 0 FAIL y 0 NOT_EVALUATED. La comprobación inicial corresponde al commit `03e1143`. La [suite completa posterior al ajuste de dependencias](reports/etapa3/revision_pr38_20261101.json) volvió a aprobar las 238 pruebas, sin omisiones, sobre `0dd8c6e`. La evaluación final de datos no se repitió.

La [actualización de compatibilidad de DeepChecks](reports/etapa3/cierre_adicional_marco.md) añade siete pruebas: la suite completa aprueba **245 pruebas**, sin fallos ni omisiones. El entorno independiente usa setuptools 84.1.0 y su auditoría de 122 requisitos no encontró vulnerabilidades conocidas. Esta actualización conserva la validación final de datos y requiere la revisión independiente de su PR para integrarse en `main`.

### Contribuciones del equipo

| Responsable | Contribución | Evidencia |
|---|---|---|
| Marco | Entorno de calidad, ingesta, seguridad, dependencias y verificación del catálogo | [Avance técnico](reports/etapa3/avance_marco.md) |
| Stefania | Ampliación de pruebas de P1, calendario, partición y revisión de seguridad | [Revisión de P1](reports/etapa3/revision_p1_stefania.md) |
| Diego Martínez | Motor DeepChecks, política de calidad, pruebas de P2 y contratos del registro | [Calidad de datos](reports/etapa3/calidad_datos_diego_martinez.md) |
| Diego Hurtado | Pruebas adicionales de P3, perfiles horarios y análisis de seguridad | [Revisión de P3](reports/etapa3/revision_p3_diego_hurtado.md) |

Las contribuciones se integraron mediante los PR #31 (P3), #33 (P1), #35 (DeepChecks/P2) y #36 (verificación del catálogo y dependencias), además de las aportaciones iniciales de infraestructura y calidad.

### Pruebas automatizadas

Las pruebas utilizan PyTest, datos sintéticos y recursos temporales para comprobar condiciones normales, casos límite y comportamientos ante errores.

La configuración central de PyTest se encuentra en `pyproject.toml`.

Para ejecutar la suite desde la raíz del repositorio, con el entorno del proyecto configurado:

Preparar también el [entorno independiente de DeepChecks](references/etapa3/deepchecks_entorno.md), incluida la adaptación de compatibilidad indicada en esa guía, para que se ejecuten las pruebas que utilizan la biblioteca.

```bash
python -m pytest tests -q
```

La ejecución combinada documentada por Diego Martínez reportó 229 pruebas aprobadas. Este resultado corresponde a las verificaciones realizadas durante el desarrollo y no sustituye la validación final independiente sobre el código integrado.

### Validación de calidad con DeepChecks

El motor se implementa en:

`mibici_equipo39/validation/data_checks.py`

La política de calidad se encuentra en:

`references/etapa3/quality_policy.json`

La política fue congelada con `frozen: true`, después de la revisión de criterios de P1 y P3 por sus responsables, sin modificar las reglas ni los umbrales acordados.

El motor identifica cuatro estados:

| Estado | Interpretación |
|---|---|
| PASS | Comprobación satisfactoria |
| WARN | Advertencia que requiere interpretación |
| FAIL | Incumplimiento del criterio definido |
| NOT_EVALUATED | Comprobación no ejecutada, con causa registrada |

La ejecución de desarrollo documentada reportó 64 PASS, 2 WARN y 1 FAIL. El FAIL se relaciona con una discrepancia de hash del catálogo de estaciones en macOS ARM, investigada y contrastada con el entorno Windows. El resultado original se conserva sin modificar los manifiestos para ocultar la diferencia.

La etapa `final` se ejecutó una sola vez sobre el código integrado y los datos oficiales, con la política congelada. El [resumen original](reports/etapa3/validacion_final_datos_20261101.json) conserva todas las comprobaciones. Las tres advertencias corresponden a variables constantes de P3 y permanecen visibles.

### Seguridad y dependencias

Se realizaron revisiones mediante Bandit, auditorías de dependencias, comprobaciones de exclusiones y análisis de seguridad de los componentes P1, P2 y P3.

Los hallazgos identificados se encuentran documentados con sus limitaciones y acciones de seguimiento. La corrección de DeepChecks atiende los dos avisos de setuptools del cierre anterior; las observaciones bajas de Bandit permanecen documentadas. Una auditoría sin vulnerabilidades conocidas no demuestra ausencia de todos los riesgos.

### Documentación y evidencias

- [Contrato de calidad de la Etapa 3](references/etapa3/contrato_calidad.md)
- [Instalación y ejecución de verificaciones](references/etapa3/ejecucion_marco.md)
- [Matriz inicial de pruebas](reports/etapa3/matriz_pruebas.md)
- [Entorno de DeepChecks](references/etapa3/deepchecks_entorno.md)
- [Hallazgos de seguridad](reports/etapa3/hallazgos.md)
- [Migración de MLflow y PyArrow](references/etapa3/migracion_mlflow_pyarrow.md)
- [Verificación de estaciones entre entornos](references/etapa3/verificacion_estaciones.md)
- [Capturas preliminares y su procedencia](reports/etapa3/evidencias_marco.md)
- [Manifiesto de evidencias](reports/etapa3/evidencias_manifest.json)
- [Consolidación de evidencias de la Etapa 3 — Diego Hurtado](reports/etapa3/evidencias_consolidadas_diego_hurtado.md)

Las capturas preliminares documentan pruebas y verificaciones anteriores a la integración completa. Sus fechas, alcance y procedencia deben conservarse y distinguirse de las capturas de la validación final.

### Pendientes del cierre integrado

Marco completó la suite integrada y la validación final desde un clon nuevo, con entornos instalados desde cero y tablas procesadas verificadas contra los manifiestos. La descarga anual no se repitió.

Los [resultados del cierre](reports/etapa3/cierre_integrado_marco_20261101.json) y la [revisión de seguridad](reports/etapa3/seguridad_cierre_20261101.json) documentan el alcance y las limitaciones de esa ejecución. Las [nueve capturas originales del cierre](reports/etapa3/capturas_finales_20261101.md) muestran los registros de pruebas, validación y seguridad, además de la integración de los PR #38 y #39. Su procedencia y alcance se conservan en el inventario. El [cierre adicional](reports/etapa3/cierre_adicional_marco.md) documenta la solución posterior para los dos avisos de DeepChecks, la suite de 245 pruebas y la captura histórica renovada.

Diego Hurtado completó la consolidación del README y las evidencias mediante los PR #40 y #41. La actualización adicional de Marco queda sujeta a revisión independiente e integración por PR.

La integración de los PR técnicos no constituye por sí misma la verificación final de calidad ni demuestra la ausencia de vulnerabilidades.

## Estado de integración de la Etapa 2

La Etapa 2 utiliza un controlador común de experimentación,
MLflow Projects y Model Registry. Los ADAPTERS de P1, P2 y P3 están integrados; P1 se incorporó mediante el PR #16.

El controlador común y el registro de modelos se integraron
mediante el PR #12. La implementación de P2 se incorporó
mediante el PR #13. Las mejoras de P3 y su conexión con
el controlador se incorporaron mediante los PR #11 y #14.

La configuración de candidatos se encuentra en
`config.STAGE2_SEARCH_PLAN`, y los puntos de entrada de
experimentación y registro están definidos en `MLproject`.

La arquitectura técnica de esta etapa se documenta en
[Arquitectura de la Etapa 2](references/etapa2/arquitectura.md).

Las condiciones del entorno y del servidor se describen en
[Contrato de infraestructura](references/etapa2/contrato_infraestructura.md).

El [punto de partida](references/etapa2/starting_point.json)
conserva los resultados históricos utilizados como referencia.
Estos resultados no sustituyen las nuevas corridas oficiales
de la Etapa 2.

Las pruebas automatizadas verifican la implementación,
pero no acreditan por sí solas la selección oficial de
modelos, su registro como champion ni la reproducción final.

### Cierre técnico del 27 de octubre de 2026

El PR #22 quedó integrado después de las revisiones de Stefania, Diego Martinez y Diego Hurtado. Las tres selecciones se reprodujeron con métricas coincidentes y los modelos se registraron como versión 1 con alias `champion`. Su carga por nombre y predicciones se comprobaron en una ejecución independiente de MLflow Projects. El PR #24 incorporó la justificación de P3 revisada por Marco.

El [PR #25](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/25), revisado e integrado por Diego Hurtado, incorporó las evidencias de reproducción y registro. El [PR #26](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/26), de Diego Hurtado y revisado e integrado por Marco, completó la [interpretación de los perfiles horarios y el mapa de P3](reports/etapa2/p3.md). Ambas actividades están cerradas.

El [cierre técnico y sus evidencias](reports/etapa2/cierre_tecnico_marco.md) conserva corridas, versiones, linaje, comandos y límites. Las [19 capturas de la interfaz](reports/etapa2/capturas_mlflow_marco.md) documentan búsquedas anidadas, comparaciones, artefactos y las tres versiones registradas con alias y linaje. Queda revisar este conjunto e incorporarlo al Word y PDF consolidados. El envío en Canvas no está verificado.

Repositorio público: https://github.com/makroem/TC5061-Proyecto-Equipo39

## Propósito y alcance
P1 estima salidas por estación en la siguiente hora; P2 aproxima riesgo de bicicletas o anclajes; P3 agrupa estaciones por uso. El código final vive en `mibici_equipo39`; los notebooks son exploratorios. Los modelos historicos de P1/P2/P3 y su evaluacion cronologica se integraron mediante los PR #8 y #3. Los tres ADAPTERS de la Etapa 2 también están integrados, incluida la aportación de P1 del PR #16. El estado de integración, las revisiones y las dependencias restantes se registran en references/cierre_marco.md.

## Equipo roles y contribuciones
Marco (`makroem`, persona1): infraestructura del proyecto, ingesta, versionado de datos, evaluación temporal, implementación inicial de P3 y coordinación de integración.

Stefania (`a01236059-lab`, persona2): propuesta de variables, ML Canvas, exploración de P1 y participación en las revisiones de integración.

Diego Martínez (`Sanciprian`, persona3): integración de variables y modelos, desarrollo de P2 para la Etapa 2, controlador común de experimentación, registro de modelos y puntos de entrada de MLflow Projects (PR #12 y #13).

Diego Hurtado (`diegoHurtado01`, persona4): preparación experimental de P3 para la Etapa 2, incorporación de variantes KMeans y Gaussian Mixture, métricas de estabilidad y costo, artefactos interpretables y pruebas automatizadas (PR #11). Implementación del ADAPTER de P3 para el controlador común (PR #14). Revisión formal del controlador y de P2 mediante los PR #12 y #13. Responsable de la documentación de arquitectura y consolidación del reporte de experimentos de la Etapa 2.

Las contribuciones integradas conservan su autoría en Git y GitHub. Las corridas oficiales, las selecciones aprobadas, su reproducción y la carga por alias se documentan en el cierre técnico, con evidencia independiente de las pruebas automatizadas.
## Preguntas y usuarios
| Pregunta | Resultado | Usuario y decisión |
|---|---|---|
| P1 Regresión | Salidas en estación durante [t,t+1 hora) | Operador, planeación de flota |
| P2 Clasificación | Dos riesgos proxy en la siguiente hora | Rebalanceo, priorizar inspecciones |
| P3 Clustering | Grupo de estación según su perfil histórico | Planeación urbana, interpretar patrones |

P2 no observa inventario. Parte de 50% de capacidad y etiqueta presión si el flujo intrahora llega a 10% o 90%. No prueba que una estación estuviera realmente vacía o llena. La capacidad/ubicación del catálogo de septiembre se usa retrospectivamente; no acredita su historial de cambios ni entra como predictor de P1/P2.

## Fuentes tamaño uso y privacidad
Fuente: https://mibici.net/es/datos-abiertos/. Doce CSV de octubre de 2025 a septiembre de 2026 y nomenclatura_2026_09.csv. Los trece enlaces exactos y SHA256 se registran en `references/data_manifest.json`. Son 4,497,877 filas originales, 4,497,119 viajes completos retenidos, 484 estaciones de catálogo y 480 con capacidad válida. La malla cruza estaciones observadas y catálogo; la elegibilidad de P1/P3 se decide solo con train.

La ingesta elimina identificadores de usuario y variables demográficas. Los originales, Parquet, modelos y almacén MLflow quedan fuera de Git. MIT cubre el código; no se atribuye a los CSV una licencia específica no identificada. Se reconoce a MiBici como fuente y no se redistribuyen CSV. Falta confirmar con el titular las condiciones adicionales antes de otros usos.

## Partición y temporalidad
`chronological_holdout` versión 3: train de octubre 2025 a mayo 2026 (243 días), validación junio-julio (61), test agosto-septiembre (61). Se eligen meses completos contiguos para que test sea posterior al ajuste, en lugar de una proporción aproximada 70/15/15. Este único holdout no mide todos los regímenes estacionales.

La data_version no cambia. Se cambia split_id y se incorpora todo octubre, sin el antiguo descarte de ocho días. `references/split_manifest_random_days_v2.json` conserva el manifiesto anterior solo como historia. El proceso normal verifica el nuevo manifiesto sin sobrescribirlo. Las ocho entradas de P1/P2 son calendario conocido al predecir; modelos, codificadores y elegibilidad se ajustan solo en train. Selección y umbrales usan validación. Test no modifica el diseño.

## Pipeline y métricas de referencia (Etapa 1)
| Pregunta | Baseline | Candidato | Selección previa a prueba |
|---|---|---|---|
| P1 | Media train estación/día/hora con respaldos | HGB Poisson y TargetEncoder train | Menor val_mae, empate baseline |
| P2 | DummyClassifier prior por riesgo | Logística balanceada por riesgo | Mayor val_macro_f1, empate baseline |
| P3 | KMeans k=3 | GaussianMixture diagonal k=3 | Mayor val_silhouette con grupos train de al menos 5%; si ninguno cumple, ninguno |

P1 evalúa MAE/RMSE. P2 evalúa precisión/recall/F1/AP, matrices de confusión y sensibilidad a ocupación 25%/75%. El umbral de P2 se busca solo en validación con recall objetivo 0.80; si ningún umbral lo alcanza se usa mayor F1. Una precisión baja puede hacer inviables los rebalanceos aunque mejore F1.

P3 genera 48 medias horarias por estación (24 laborales y 24 de fin de semana), incluyendo ceros. Normaliza cada tipo de día a suma uno y ajusta StandardScaler solo con train. Exige 100 viajes de train. Las coordenadas no entran al agrupamiento. Evalúa silhouette, Davies Bouldin, tamaño de grupos y estabilidad ARI con cinco remuestreos de días train. El mapa es un diagrama de puntos sin base cartográfica; los grupos no prueban causas o impacto urbano.

## Estructura arquitectura y herramientas
La estructura original se generó con ccds 2.3.0, include_code_scaffold Yes (evidencia histórica en main). `data/` es local; `notebooks/` exploración; `mibici_equipo39/` código; `models/` modelos locales; `references/` manifiestos/Canvas/diagrama; `reports/` reportes/figuras. El diagrama está en `references/arquitectura.svg` y el Canvas en `references/ml_canvas.md`.

Python 3.11.9/pandas permiten funciones y bloques de 100,000 filas; PyArrow/Parquet tablas tipadas por mes; scikit-learn pipelines y métricas; MLflow trazabilidad de experimentos; GitHub revisión y autoría. `config.py` centraliza rutas, fechas, semillas e hiperparámetros. Las referencias oficiales sustentan las herramientas; falta relacionarlas con las lecturas asignadas del curso cuando estén disponibles.

## Instalación
Requiere Git y Python 3.11.9. Comprueba primero sus versiones y reutiliza las instalaciones disponibles. Clona la rama main integrada:

```bash
git clone --branch main https://github.com/makroem/TC5061-Proyecto-Equipo39.git
cd TC5061-Proyecto-Equipo39
python -m venv .venv
```

Activa `.venv` con `.venv\Scripts\Activate.ps1` en PowerShell o `source .venv/bin/activate` en Linux/macOS:

```bash
python -m pip install -r requirements.txt
python -m pip install --no-deps -e .
python -m pip check
```

requirements.txt fija versiones; pywin32 solo aplica a Windows. Se recomiendan OMP_NUM_THREADS=4, OPENBLAS_NUM_THREADS=4 y MKL_NUM_THREADS=4 para limitar recursos, sin cambiar semillas o partición. La ingesta descarga unos 390 MB y requiere espacio adicional para Parquet/tablas.

## Ingesta variables y pruebas
Desde la raíz y con el entorno activado:

```bash
python -m mibici_equipo39.dataset --verify-manifest
python -m mibici_equipo39.features
python -m pytest tests -q
```

La ingesta descarga sin pasos manuales, normaliza columnas/codificación/fechas, comprueba trece fuentes y hashes lógicos. `--freeze-manifest` solo se usa para aprobar una versión nueva de datos. Las pruebas cubren temporalidad, aislamiento, manifiestos, proxy P2, perfiles P3 y trazabilidad. Si el temporal del sistema tiene permisos incorrectos, usa una carpeta nueva con `--basetemp=../pytest-mibici-nuevo`.


## Experimentación de la Etapa 2 con MLflow Projects

La Etapa 2 utiliza el punto de entrada `train` de `MLproject` y el
controlador `mibici_equipo39.modeling.stage2`.

El controlador recibe la pregunta (`p1`, `p2` o `p3`), el modelo,
los hiperparámetros, el integrante responsable y el modo de ejecución.

### Configuración de MLflow

Esta rama utiliza MLflow 3.17.2 y PyArrow 23.0.1. Antes de conectar el entorno nuevo a una base existente de MLflow 2, seguir el [procedimiento de migración sobre una copia](references/etapa3/migracion_mlflow_pyarrow.md). El servidor oficial anterior no se actualiza automáticamente con la instalación de estas dependencias.

El 30 de octubre de 2026 se activó y verificó el servidor local migrado después de
integrar el PR #32. Se conservaron 34 corridas, 500 archivos de artefactos y los
tres modelos `champion`; el almacén anterior y el respaldo permanecen intactos.
El [registro de activación](reports/etapa3/activacion_servidor_20261030.json)
documenta el alcance y los horarios. El endpoint `http://127.0.0.1:5000` corresponde
a la máquina que aloja el servicio; la pausa de escrituras ya terminó.

El repositorio debe estar limpio y los datos procesados y manifiestos
deben encontrarse disponibles antes de iniciar una búsqueda.

En PowerShell, para utilizar el servidor configurado según el
contrato de infraestructura:

```powershell
$env:MLFLOW_TRACKING_URI = "http://127.0.0.1:5000"
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
$env:MIBICI_RESULTS_DIR = Join-Path $env:LOCALAPPDATA "MiBiciEquipo39\resultados"
```

El servidor debe estar iniciado y el usuario debe contar con acceso
al almacén correspondiente. Las corridas de prueba no sustituyen
las corridas oficiales del equipo.

### Búsqueda de modelos

Ejemplo de búsqueda de P3 ejecutada por Diego Hurtado:

```powershell
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p3 -P model=search -P member=DiegoHurtado -P mode=search
```

La búsqueda compara el baseline y las tres variantes candidatas
configuradas en `config.STAGE2_SEARCH_PLAN`.

Los modelos se ajustan con train y se seleccionan con validation.
Antes de consultar test, la selección se registra en
`evaluation/selection_before_test.json`.

Si ninguna variante cumple la regla de elegibilidad, la búsqueda
termina sin evaluar test.

### Calibración de P2

P2 utiliza `fit(train)` y posteriormente `calibrate(validation)` antes de seleccionar la variante y evaluar test. Se establecen umbrales independientes para bicicletas y anclajes, priorizando precisión con recall mínimo de 0.80 y utilizando F1 como alternativa cuando ningún umbral cumple.

La calibración se registra antes de test. En una reproducción se reutilizan los umbrales congelados en `references/etapa2/selection.json`.

### Reproducción de una selección aprobada

La reproducción requiere el archivo oficial
`references/etapa2/selection.json`, que contiene la variante y
sus hiperparámetros congelados.

```powershell
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p3 -P model=selected -P member=DiegoHurtado -P mode=reproduce
```

Este procedimiento no realiza una nueva búsqueda ni modifica
los hiperparámetros utilizando test.

### Desempate por costo de P3

El PR #18 integró al controlador común el contrato
`tie_break()` para resolver empates mediante criterios
específicos de cada ADAPTER, preservando la prioridad
del baseline.

El PR #19 implementó e integró esta regla en P3:
entre candidatos elegibles con igual métrica de selección,
se prioriza el menor tiempo de inferencia por 1,000
observaciones de validación y posteriormente el menor
tamaño serializado del modelo. El conjunto test no
participa en el desempate.

El PR #19 fue aprobado por Marco e integrado en `main` mediante el commit `4ad9e03`.


### Reproducción completa y registro

La [guía de reproducción](reports/etapa2/reproduccion.md) describe instalación, almacén independiente, validación y límites de disponibilidad de los datos. Con el entorno fijo instalado y las variables de tracking configuradas:

```powershell
mlflow run . -e reproduce --env-manager local --experiment-name mibici-equipo39 -P member=Marco -P approved_registry_uri=sqlite:///private_tracking/reproduccion.db
```

El punto de entrada encadena ingesta, reproducción de las tres selecciones, registro y carga por alias. Obtiene los identificadores de las corridas recién generadas; no requiere `Read-Host` ni copiar un `run_id`. `references/etapa2/selection.json` ya contiene las selecciones aprobadas y sus umbrales. No se edita durante una reproducción.

El registro está bloqueado por defecto. `approved_registry_uri` autoriza expresamente el destino y debe coincidir exactamente con `MLFLOW_REGISTRY_URI` (o con el tracking si no se definió un Registry separado). El valor literal del ejemplo autoriza solo la base independiente indicada: una configuración hacia el servidor oficial se rechaza antes de iniciar los pasos. MLflow Projects puede crear la corrida contenedora antes de esa comprobación, pero no se inicia la ingesta ni se registran modelos o cambian alias. El parámetro se registra en MLflow; no incluir credenciales en la URI.

El registro se realiza en el almacén configurado. Para una comprobación usar una base independiente, como indica la guía, y no el servidor oficial. El 2 de noviembre de 2026 la descarga nueva del catálogo respondió 404; la prueba con copias históricas verificadas no elimina esa limitación externa.

### Reporte corregido

El [reporte editable](reports/etapa2/ReporteParte2_MLflow_Equipo39.docx) y su [PDF](reports/etapa2/TC5061_Reporte_MLFlow_Equipo39.pdf) integran las tablas y capturas oficiales, el análisis de costo y estabilidad y la distinción entre evidencia histórica y validación del flujo actual. Las correcciones se implementan por Marco y su revisión independiente corresponde a Diego Hurtado.

### Evidencia y resultados

MLflow conserva las corridas padre e hijas, métricas, parámetros,
etiquetas, modelos, firmas y artefactos de interpretación.

Las búsquedas y reproducciones generan resúmenes en el directorio
privado configurado por `MIBICI_RESULTS_DIR`.

Las evidencias oficiales deben identificar el commit, la versión
de los datos, la partición, las corridas y el modelo seleccionado.

### Compatibilidad con la primera entrega

Los puntos de entrada históricos `p1`, `p2`, `p3` y `main` siguen
disponibles en `MLproject`. No sustituyen al controlador `train`
de la Etapa 2.

La arquitectura y sus componentes se describen en
[Arquitectura de la Etapa 2](references/etapa2/arquitectura.md).


## Git GitHub y buenas prácticas
main está protegida: una aprobación, descarte de aprobaciones antiguas y conversaciones resueltas; force push y eliminación bloqueados también para administradores. Todo cambio hacia main debe pasar por PR revisado. Ramas feat/fix/docs/chore y commits con esos prefijos. Cada persona debe abrir un PR y revisar otro; una ejecución de Marco no sustituye la evidencia de otros.

El PR #8 se incorporó a la rama de integración y el PR #3 se incorporó a main en el commit de5d622707254e275369d3e7c60d340523ce33ce. El PR #5 se cerró sin merge para evitar sobrescribir la versión consolidada. Las contribuciones y revisiones conservan su historial. Los PR #6/#7 anteriores entraron a esa rama sin revisión formal registrada; no se declara una revisión inexistente ni se evade la protección. Los notebooks antiguos con días aleatorios son historia exploratoria y no acreditan las métricas cronológicas.

## Resultados limitaciones y cierre
La propuesta consolidada está disponible en [PDF](reports/TC5061_Propuesta_Proyecto_Equipo39.pdf) y [Word editable](reports/TC5061_Propuesta_Proyecto_Equipo39.docx). El [informe de cierre y pendientes](reports/Cierre_Actividades_y_Pendientes.txt) distingue las actividades integradas de la colaboración individual restante, las lecturas y las condiciones de uso por confirmar. El envío en Canvas no está verificado en GitHub. Ambos documentos incluyen el enlace público al repositorio; el código consolidado se consulta en main. El registro de Marco está en [references/cierre_marco.md](references/cierre_marco.md).

Las métricas históricas de la primera entrega se documentan en el resumen y el PDF. No constituyen resultados oficiales de la Etapa 2. No deben mezclarse con mibici-equipo39-revision-marco, de días aleatorios. Se requieren capturas de lista, detalle con parámetros/métricas/etiquetas, artefacto y comparación, además de estructura del repositorio y referencias APA 7.

La ejecución de cierre terminó el 18 de octubre de 2026 desde MLflow Projects, en el commit ad74ba344bdfe6770a12ef37577fa7403c54dbc6, con seis runs finalizados, git_dirty=false y 39 pruebas aprobadas. La evidencia está en reports/cierre_experimentos.json y references/evidence/.

Resultados: P1 conserva baseline (val_mae 0.888775; test_mae 0.916381; test_rmse 1.718234). P2 selecciona logística (val_macro_f1 0.042048; test_macro_f1 0.051779); en test, recall de bicicletas 0.8541 y de anclajes 0.7932, con precisión 0.0218/0.0318. P3 selecciona GMM para 369 estaciones (val_silhouette 0.026594; test_silhouette 0.051373; ARI medio de remuestreo train 0.637608). Los grupos se superponen y no se presume que estén suficientemente separados para decisiones operativas.

Limitaciones: proxy P2 sin inventario, capacidad/ubicación retrospectivas de septiembre, estaciones nuevas sin train excluidas, un año de fuentes y un holdout temporal. No hay despliegue ni impacto operativo demostrado. Las aportaciones de Diego Hurtado se integraron mediante los PR #11 y #14. La selección oficial, la reproducción y el registro de la Etapa 2 se documentan por separado en el [cierre técnico](reports/etapa2/cierre_tecnico_marco.md).

## Relación parcial con las lecturas
La introducción pública de Wilson, capítulo 6, respalda la comparación objetiva de alternativas; se conserva el baseline de P1 aunque exista un candidato más complejo. La vista pública de Thompson, capítulo 7, distingue crear un modelo de demostrar su utilidad y enumera seguimiento de experimentos y repositorios en 7.4.2; se aplica con MLflow y con límites operativos explícitos. Solo se consultaron estas vistas públicas, no los capítulos completos ni Lauchande 5 o Huyen 6. Falta contrastar las cuatro lecturas asignadas.

- Wilson: https://livebook.manning.com/book/machine-learning-engineering-in-action/chapter-6
- Thompson: https://livebook.manning.com/book/managing-machine-learning-projects/chapter-7

## Etapa 4: preparación del modelo para la API

Marco preparó la recuperación y carga verificadas de P1. El [contrato inicial](references/etapa4/contrato_api.md) distribuye esquemas, API y contenedor entre los cuatro integrantes. La API HTTP y la imagen OCI todavía requieren esos módulos; esta sección documenta lo que ya se puede ejecutar.

### Entorno de servicio

Comprueba primero `python --version` (3.11.9) y si ya existe `.venv-api`. Solo si falta, créalo. Después instala las versiones fijadas:

```powershell
python -m venv .venv-api
$pythonApi = '.venv-api\Scripts\python.exe'
& $pythonApi -m pip install -r requirements-api-dev.txt
& $pythonApi -m pip check
```

`requirements-api.txt` usa MLflow Skinny 3.17.2 para cliente y carga local, más las dependencias de P1 y FastAPI. No instala un servidor de tracking. El servidor oficial conserva su entorno completo anterior. El modelo mantiene intacto su archivo histórico de dependencias; MLflow puede advertir diferencias con ese entorno. Se comprobó paridad en el entorno de servicio de Windows; la imagen Linux debe verificarse durante su construcción.

### Recuperar exactamente el modelo aprobado

Usa el servidor oficial iniciado según la sección de MLflow; `127.0.0.1` se refiere a la computadora que aloja ese servidor. Otro integrante necesita acceso autorizado al mismo Registry y sus artefactos, no una base vacía. No hay un servidor público compartido configurado por esta entrega.

```powershell
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
& $pythonApi -B -m mibici_equipo39.serving.export_model --manifest references/etapa4/model_manifest.json --output models/serving/p1
& $pythonApi -B -m mibici_equipo39.serving.verify_model
```

El primer comando descarga la versión numérica fijada y verifica las 22 huellas. Si ya está presente, comprueba el paquete sin sobrescribirlo. El segundo compara 72 entradas de calendario con una carga independiente por nombre y versión desde el Registry, verifica repetición y prueba la carga local con solicitudes de red bloqueadas. No solicita un run_id ni ejecuta entrenamiento.

Para preparar una selección nueva se utiliza `--name mibici-equipo39-p1-demanda --alias champion --output <destino-nuevo> --manifest-out <manifiesto-nuevo>`, después de una revisión del cambio. No sobrescribas el manifiesto de esta entrega para seguir un alias que haya cambiado.

### Pruebas y seguridad del arranque

```powershell
& $pythonApi -B -m pytest tests/api --confcutdir=tests/api -q
& $pythonApi -m bandit -r mibici_equipo39/serving -f json -o reports/etapa4/bandit_api.json
& $pythonApi -m pip_audit --no-deps --disable-pip -r requirements-api.txt -f json -o reports/etapa4/pip_audit_api.json
```

`--confcutdir` mantiene las pruebas unitarias de servicio independientes de las fixtures de entrenamiento de la etapa anterior. Si Windows impide crear temporales, agrega `--basetemp=private_results/etapa4/pruebas-nueva-carpeta` y utiliza un nombre que todavía no exista. La suite anterior se ejecuta con el entorno completo de calidad, no con el entorno reducido de servicio.

Resultados y límites: [arranque de Marco](reports/etapa4/arranque_marco.md), [paridad real](reports/etapa4/paridad_modelo_marco.json) y [revisión de seguridad](reports/etapa4/seguridad_api.md). La comparación local no sustituye la predicción desde el contenedor que debe documentarse al integrar FastAPI.

La [captura E02 del Registry de P1](reports/etapa4/captura_registry_p1.md) muestra la versión 1, el alias `champion` y su linaje. Se conserva la imagen original proporcionada por Marco el 2 de noviembre de 2026, junto con su huella SHA-256.

### Recuperación del catálogo histórico

El 3 de noviembre de 2026 el portal enlaza el catálogo de octubre y la URL de septiembre responde 404. Se conserva septiembre para reproducir el modelo aprobado. Una copia histórica verificada permite continuar sin cambiar datos, partición ni modelos.

`MIBICI_SOURCE_CACHE` indica una carpeta externa al repositorio que contiene `nomenclatura_2026_09.csv`. En PowerShell, usa la ruta real de tu respaldo:

```powershell
$env:MIBICI_SOURCE_CACHE = 'D:\RespaldoEquipo39'
python -B -m mibici_equipo39.prepare_catalog
mlflow run . -e ingest --env-manager local
```

El primer comando Python comprueba únicamente el catálogo; es opcional. La ingesta y el flujo `reproduce` aplican la misma recuperación automáticamente. El orden es: archivo local verificado, copia de la carpeta configurada, fuente oficial y, si falla, `MIBICI_STATIONS_BACKUP_URL`. Esta última debe ser una descarga HTTPS del mismo archivo, nunca la página de vista previa de una carpeta. Configurar su valor fuera de Git; no incluir credenciales en el código ni en capturas. Una URL que requiera autenticación interactiva no funciona como descarga automática.

La copia y la URL alternativas requieren el SHA256 congelado; un respaldo alterado se rechaza. El modo `freeze` conserva la descarga oficial y no adopta respaldos. Los CSV permanecen fuera de Git. Todavía debe acordarse la ubicación compartida para que otro equipo sin la copia local pueda descargarla. Ver [recuperación comprobada](reports/etapa4/recuperacion_catalogo_20261103.md).
