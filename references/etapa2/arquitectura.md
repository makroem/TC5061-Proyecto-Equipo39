# Arquitectura del sistema de experimentación — Etapa 2



**Proyecto:** MiBici — Equipo 39

**Curso:** TC5061

**Responsable de documentación:** Diego Hurtado

**Fecha:** 25 de octubre de 2026



## 1. Objetivo



Documentar la arquitectura del sistema de experimentación, evaluación, registro y reproducción de modelos de aprendizaje automático de la Etapa 2.



La solución utiliza MLflow Projects y MLflow Tracking para ejecutar experimentos trazables, comparar un modelo baseline con tres variantes candidatas por pregunta y conservar los modelos y artefactos necesarios para su reproducción.



Las tres preguntas abordadas son: P1, predicción de demanda; P2, clasificación de riesgos aproximados de bicicletas y anclajes; y P3, agrupamiento de estaciones por patrones de uso.



## 2. Diagrama general de arquitectura



```mermaid

flowchart TD

&#x20;   A["Datos abiertos MiBici<br/>12 CSV de viajes y catálogo"] --> B["dataset.py<br/>Ingesta, limpieza y verificación"]

&#x20;   B --> C["data/raw, external y processed"]

&#x20;   B --> D["data_manifest.json<br/>Versión de datos"]

&#x20;   C --> E["features.py<br/>Variables y partición cronológica"]

&#x20;   E --> F["Tablas procesadas<br/>Train / Validation / Test"]

&#x20;   E --> G["split_manifest.json<br/>Versión de partición"]



&#x20;   F --> H["MLflow Projects<br/>MLproject: train"]

&#x20;   H --> I["stage2.py<br/>Controlador común"]

&#x20;   I --> J["QuestionAdapter P1"]

&#x20;   I --> K["QuestionAdapter P2"]

&#x20;   I --> L["QuestionAdapter P3"]



&#x20;   J --> M["Baseline + 3 candidatos"]

&#x20;   K --> M

&#x20;   L --> M



&#x20;   M --> N["Ajuste con train<br/>Evaluación con validation"]

&#x20;   N --> O{"¿Existe variante elegible?"}

&#x20;   O -->|No| P["Búsqueda detenida<br/>Sin consultar test"]

&#x20;   O -->|Sí| Q["Selección congelada<br/>selection_before_test.json"]

&#x20;   Q --> R["Evaluación final con test"]

&#x20;   R --> S["MLflow Tracking<br/>Runs, métricas y artefactos"]

&#x20;   S --> T["Revisión de selección oficial"]

&#x20;   T --> U["Model Registry<br/>Alias champion"]

&#x20;   U --> V["Verificación de carga<br/>y reproducción"]



&#x20;   D -.-> I

&#x20;   G -.-> I

&#x20;   W["Git y GitHub<br/>Commit, PR y revisión"] -.-> I

&#x20;   W -.-> S

```



El diagrama representa el flujo implementado. La ejecución oficial, la asignación de alias y la validación final deben acreditarse mediante sus propias evidencias.



## 3. Capas de la arquitectura



### 3.1 Ingesta y almacenamiento



El módulo `mibici_equipo39/dataset.py` procesa los datos abiertos de MiBici correspondientes a octubre de 2025 a septiembre de 2026, junto con el catálogo de estaciones.



El sistema organiza los archivos originales y procesados dentro de `data/`. El manifiesto `references/data_manifest.json` permite verificar la identidad y versión de las fuentes utilizadas.



Los archivos de datos voluminosos se conservan fuera del control de versiones de Git.



### 3.2 Ingeniería de variables y partición



El módulo `mibici_equipo39/features.py` construye las tablas de entrenamiento y evaluación y aplica la estrategia `chronological_holdout`.



| Conjunto | Periodo | Uso |

|---|---|---|

| Entrenamiento | Octubre 2025 – mayo 2026 | Ajuste de modelos y transformaciones |

| Validación | Junio – julio 2026 | Comparación y selección |

| Prueba | Agosto – septiembre 2026 | Evaluación final de desempeño |



La partición se registra en `references/split_manifest.json` y se verifica antes de utilizarse. Los procedimientos de ajuste no deben aprender de los periodos futuros.



### 3.3 Controlador común de experimentación



El módulo `mibici_equipo39/modeling/stage2.py` implementa el controlador parametrizado de la Etapa 2.



Cada pregunta dispone de un ADAPTER compatible con `QuestionAdapter`. Esta interfaz proporciona métodos para definir el baseline, cargar datos, ajustar variantes, evaluar particiones, generar ejemplos y producir gráficas.



El controlador permite reutilizar el mismo flujo experimental en P1, P2 y P3 sin combinar sus objetivos ni sus criterios de evaluación.



### 3.4 Modelos y búsqueda de variantes



El plan de experimentación está centralizado en `config.STAGE2_SEARCH_PLAN`.



| Pregunta | Baseline | Tres candidatos | Criterio principal |

|---|---|---|---|

| P1 | Baseline de demanda | HGB 100, HGB 200, Random Forest 300 | Menor `val_mae` |

| P2 | DummyClassifier | Regresión logística C=0.1, C=1 y C=10 | Mayor `val_macro_f1` |

| P3 | KMeans k=3 | KMeans k=4, KMeans k=5 y GMM de 3 componentes | Mayor `val_silhouette`, con elegibilidad |



Para P3, las estaciones se representan mediante 48 características de uso horario: 24 correspondientes a días laborales y 24 a fines de semana.



El modelo completo incorpora `StandardScaler` y el algoritmo de clustering en un `Pipeline`. Las transformaciones se ajustan exclusivamente con entrenamiento.



P3 también calcula la estabilidad mediante ARI utilizando remuestreos de días de entrenamiento. La elegibilidad exige una proporción mínima de grupo de 5%.



### 3.5 Separación de selección y evaluación final



El controlador ajusta los modelos con entrenamiento y utiliza validación para comparar alternativas.



Una vez seleccionada la variante elegible, registra la decisión y sus métricas de validación en `evaluation/selection_before_test.json`, antes de evaluar test.



Si no existe una variante elegible, la búsqueda se detiene sin consultar test. Si existe una selección válida, el controlador evalúa los modelos en el conjunto reservado y registra las métricas correspondientes.



Esta separación evita utilizar el conjunto de prueba para elegir el modelo o modificar sus hiperparámetros.



## 4. MLflow Projects y trazabilidad



El archivo `MLproject` define los puntos de entrada de la experimentación.



`ingest` prepara los datos, `train` ejecuta la búsqueda o reproducción de una pregunta, `registry` registra modelos seleccionados y `verify_registry` comprueba su carga.



Los puntos de entrada históricos `p1`, `p2`, `p3` y `main` también se conservan.



En una búsqueda de Etapa 2, MLflow Projects crea una corrida padre. El controlador registra corridas hijas para el baseline y las variantes candidatas.



Cada corrida incorpora parámetros, métricas y etiquetas de trazabilidad, incluyendo el identificador del equipo, la pregunta, el ejecutor, el autor del código, el commit de Git y las versiones de datos y partición.



Los modelos se guardan junto con su firma, ejemplo de entrada, configuración, métricas, predicción de ejemplo y artefactos de interpretación.



## 5. Model Registry y reproducción



El módulo `mibici_equipo39/registry.py` gestiona el registro de los modelos seleccionados.



Antes del registro se comprueba la correspondencia entre la corrida, la selección aprobada, las versiones de datos, el estado de Git y la pregunta correspondiente.



El modelo registrado se carga y su predicción se contrasta con la evidencia guardada. El alias `champion` se asigna después de esta verificación.



El alias identifica la versión seleccionada dentro del proyecto académico. No implica que exista un servicio de inferencia desplegado en producción.



La reproducción utiliza una selección y configuración previamente aprobadas, sin volver a elegir hiperparámetros a partir de test.



## 6. Almacenamiento, colaboración y seguridad



GitHub conserva el código, los manifiestos y la documentación mediante ramas y pull requests sujetos a revisión.



MLflow almacena las corridas, parámetros, métricas, modelos y artefactos experimentales. El servidor oficial puede utilizar un backend SQLite y un destino separado para artefactos, según el contrato de infraestructura.



Los resultados temporales pueden dirigirse fuera del repositorio mediante `MIBICI_RESULTS_DIR`. No se deben publicar bases de MLflow, archivos de viajes, credenciales ni identificadores personales.



La trazabilidad requiere vincular cada corrida oficial con un commit identificable y un repositorio sin cambios pendientes.



## 7. Limitaciones y estado de validación



La infraestructura permite comparar y registrar modelos, pero los resultados dependen de la calidad de los datos, de la partición temporal y de la definición de cada pregunta.



P2 utiliza etiquetas aproximadas y no observa directamente el inventario real de bicicletas o anclajes. En P3, obtener grupos estadísticos no demuestra por sí mismo su utilidad operativa.



Las pruebas automatizadas verifican contratos y comportamiento del código, pero no sustituyen las corridas oficiales, la selección documentada, el registro efectivo de los modelos ni las evidencias de reproducción.



## 8. Archivos técnicos de referencia



| Componente | Ubicación |

|---|---|

| Configuración | `mibici_equipo39/config.py` |

| Ingesta | `mibici_equipo39/dataset.py` |

| Variables | `mibici_equipo39/features.py` |

| Controlador | `mibici_equipo39/modeling/stage2.py` |

| Adaptadores | `mibici_equipo39/modeling/p1.py`, `p2.py`, `p3.py` |

| Registro | `mibici_equipo39/registry.py` |

| Tracking | `mibici_equipo39/modeling/tracking.py` |

| Ejecución | `MLproject` |

| Contrato de infraestructura | `references/etapa2/contrato_infraestructura.md` |

| Manifiestos | `references/data_manifest.json` y `references/split_manifest.json` |



Esta arquitectura describe las responsabilidades de los componentes y los mecanismos de trazabilidad. Los resultados cuantitativos y la evidencia final se incorporarán al reporte de experimentos de la Etapa 2.
