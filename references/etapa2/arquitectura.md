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

    A["Datos abiertos MiBici<br/>12 CSV de viajes y catálogo"] --> B["dataset.py<br/>Ingesta, limpieza y verificación"]

    B --> C["data/raw, external y processed"]

    B --> D["data_manifest.json<br/>Versión de datos"]

    C --> E["features.py<br/>Variables y partición cronológica"]

    E --> F["Tablas procesadas<br/>Train / Validation / Test"]

    E --> G["split_manifest.json<br/>Versión de partición"]



    F --> H["MLflow Projects<br/>MLproject: train"]

    H --> I["stage2.py<br/>Controlador común"]

    I --> J["QuestionAdapter P1"]

    I --> K["QuestionAdapter P2"]

    I --> L["QuestionAdapter P3"]



    J --> M["Baseline + 3 candidatos"]

    K --> M

    L --> M



    M --> N["Ajuste con train<br/>Evaluación con validation"]

    N --> O{"¿Existe variante elegible?"}

    O -->|No| P["Búsqueda detenida<br/>Sin consultar test"]

    O -->|Sí| Q["Selección congelada<br/>selection_before_test.json"]

    Q --> R["Evaluación final con test"]

    R --> S["MLflow Tracking<br/>Runs, métricas y artefactos"]

    S --> T["Revisión de selección oficial"]

    T --> U["Model Registry<br/>Alias champion"]

    U --> V["Verificación de carga<br/>y reproducción"]



    D -.-> I

    G -.-> I

    W["Git y GitHub<br/>Commit, PR y revisión"] -.-> I

    W -.-> S

```



El diagrama representa la arquitectura objetivo. Los ADAPTERS de P2 y P3 estan integrados, mientras que P1 depende del PR #16. La ejecucion conjunta de las tres preguntas aun requiere verificar esa integracion. La ejecución oficial, la asignación de alias y la validación final deben acreditarse mediante sus propias evidencias.



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



La arquitectura contempla un ADAPTER por pregunta compatible con `QuestionAdapter`. P2 y P3 estan integrados; P1 continua pendiente del PR #16. Esta interfaz proporciona métodos para definir el baseline, cargar datos, ajustar variantes, evaluar particiones, generar ejemplos y producir gráficas.



El controlador permite reutilizar el mismo flujo experimental en P1, P2 y P3 sin combinar sus objetivos ni sus criterios de evaluación. La ejecucion consolidada de P1, P2 y P3 requiere integrar y verificar primero el ADAPTER de P1.



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

**Calibración de P2 en la Etapa 2.**

El `P2Adapter` separa el entrenamiento de los modelos y la calibración de sus umbrales. `fit()` utiliza exclusivamente `train` para ajustar dos clasificadores independientes: riesgo de bicicletas (`bikes`) y riesgo de anclajes (`docks`).

Después, `calibrate()` utiliza `validation` para establecer un umbral por riesgo. Examina valores de 0.05 a 0.95 en incrementos de 0.05. Prioriza la mayor precisión cuando `recall >= 0.80`; si ningún umbral cumple, selecciona el mayor F1. En caso de empate, utiliza el umbral más alto.

El controlador sigue la secuencia `fit(train) -> calibrate(validation) -> evaluate(validation) -> seleccion -> evaluate(test)`. Antes de consultar test, registra la variante elegida, las métricas de validación y los umbrales en `evaluation/selection_before_test.json`.

Los umbrales quedan incorporados al modelo `P2RiskModel`. Durante una reproducción se reutilizan los valores congelados en `references/etapa2/selection.json`, sin volver a optimizarlos con validación. Si faltan los umbrales de alguno de los dos riesgos, la reproducción se rechaza.

El conjunto test permanece reservado hasta después de la selección.



El controlador ajusta los modelos con entrenamiento y utiliza validación para comparar alternativas.



Una vez seleccionada la variante elegible, registra la decisión y sus métricas de validación en `evaluation/selection_before_test.json`, antes de evaluar test.



Si no existe una variante elegible, la búsqueda se detiene sin consultar test. Si existe una selección válida, el controlador evalúa los modelos en el conjunto reservado y registra las métricas correspondientes.



Esta separación evita utilizar el conjunto de prueba para elegir el modelo o modificar sus hiperparámetros.



### 3.6 Desempate por costo de P3

El PR #18 incorporó al controlador común el mecanismo
`QuestionAdapter.tie_break()` para resolver empates mediante
criterios definidos por cada pregunta. El baseline conserva
prioridad cuando participa en un empate.

En P3, el criterio principal sigue siendo maximizar
`val_silhouette`, considerando solamente las variantes que
cumplen la elegibilidad de un grupo mínimo del 5%.
Cuando dos candidatos empatan en la métrica de selección,
la implementación integrada de `P3Adapter.tie_break()` utiliza, en orden:

1. Menor tiempo de inferencia por cada 1,000 observaciones,
   medido con perfiles de validación.
2. Menor tamaño serializado del modelo.

El tiempo de ajuste se registra como métrica de costo,
pero no sustituye el criterio de desempate anterior.
Ni la selección ni la medición del desempate
consultan el conjunto test.

La implementación de P3 y sus pruebas de desempate fueron aportadas por Diego Hurtado mediante el PR #19, commit `ff31bee`. Marco aprobó la revisión tras verificar 50 pruebas de P3 y del controlador, sin fallos. El PR fue integrado en `main` mediante el commit `4ad9e03`. Esta verificación no acredita corridas oficiales ni registro del modelo ganador.

La validación local reportada incluye 33 pruebas de P3
aprobadas y 114 pruebas del repositorio aprobadas con
una prueba de P2 excluida por un fallo independiente de
carga de artefactos MLflow en Windows.


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
