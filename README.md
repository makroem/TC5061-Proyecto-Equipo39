# Proyecto MiBici Equipo 39

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

El [cierre técnico y sus evidencias](reports/etapa2/cierre_tecnico_marco.md) conserva corridas, versiones, linaje, comandos y límites. Quedan por completar las capturas legibles de la interfaz y la consolidación del reporte. Las capturas deben mostrar la comparación con corridas anidadas, los artefactos de una candidata y las tres versiones registradas con alias y linaje. El envío en Canvas no está verificado.

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


### Registro de modelos

Después de contar con una selección oficial aprobada, el punto
de entrada `registry` permite registrar la corrida seleccionada.

```powershell
mlflow run . -e registry --env-manager local --experiment-name mibici-equipo39 -P question=p3 -P source_run_id=ID_REAL_DEL_RUN
```

`ID_REAL_DEL_RUN` debe sustituirse por el identificador real de la
corrida seleccionada. No es un comando que deba ejecutarse antes
de disponer de dicha selección.

El registro verifica trazabilidad, versiones y carga del modelo
antes de asignar el alias `champion`.

### Verificación del Model Registry

```powershell
mlflow run . -e verify_registry --env-manager local --experiment-name mibici-equipo39
```

La verificación carga los modelos registrados por alias y contrasta
sus predicciones con los ejemplos almacenados.

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
