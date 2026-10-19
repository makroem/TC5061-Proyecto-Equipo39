# TC5061 Proyecto MiBici, Equipo 39

Propuesta de Machine Learning sobre el sistema de bicicleta pública MiBici (Guadalajara) y su base reproducible: ingesta versionada, variables, experimentos base y registro en MLflow.

## Preguntas

| # | Pregunta | Tarea | Usuario |
|---|---|---|---|
| P1 | ¿Cuántos viajes iniciarán en cada estación en la siguiente hora? | Regresión | Operador del sistema, para planear la flota |
| P2 | ¿Una estación estará en riesgo de quedarse sin bicicletas o sin anclajes en la siguiente hora? | Dos clasificaciones binarias | Equipo de rebalanceo |
| P3 | ¿Qué grupos de estaciones comparten patrones de uso y dónde están? | Clustering | Planeación urbana y expansión |

P2 es una aproximación: MiBici no publica inventario, así que el riesgo se construye con los viajes y la capacidad publicada (ocupación inicial hipotética de 50%, umbrales de 10% y 90%).

## Datos

- Fuente: [datos abiertos de MiBici](https://mibici.net/es/datos-abiertos/), con 12 CSV mensuales (octubre de 2025 a septiembre de 2026) y `nomenclatura_2026_09.csv`.
- Volumen: 4,497,877 filas originales y 4,497,119 viajes retenidos; 484 estaciones en el catálogo, 480 con capacidad válida.
- Versión de datos: `data_version` e9de13df..., en `references/data_manifest.json`, con el SHA-256 de cada fuente.
- Partición: días completos al azar estratificados por mes, 70/15/15 y semilla 39 (252/52/53 días). `references/split_manifest.json` guarda el mapa y su `split_id`; la construcción lo verifica y no lo reescribe.
- X solo lleva variables de calendario: con días al azar, los rezagos meterían objetivos de días reservados en train.
- Uso y privacidad: ver `references/data_usage.md`. No se versionan datos, modelos ni carpetas de MLflow.

## Estructura

```text
mibici_equipo39/
  config.py           rutas, fechas, semilla e hiperparámetros
  dataset.py          descarga, limpieza por bloques, Parquet y manifiesto SHA-256
  features.py         malla estación-hora, calendario, partición y etiquetas de P2
  plots.py            gráficas registradas como artefactos
  modeling/
    p1.py, p2.py      experimentos por pregunta (baseline y candidato)
    tracking.py       parámetros, etiquetas y runs anidados en MLflow
    train.py          controlador común
notebooks/            exploración y refactorización (convención 1.x-iniciales-descripcion)
  refactorizado/      versión vigente de variables y P1
references/           manifiestos, ML Canvas, uso de datos y ejecución
reports/              reportes agregados y figuras
tests/                pruebas de ingesta, variables, aislamiento y P2
MLproject             entry points de MLflow Projects
```

Flujo de notebooks: `1.x` explora, `2.x` refactoriza en funciones y clases, y el resultado pasa al módulo. La versión vigente es esta:

- Variables: `1.0-p2-exploracion-mibici` y `refactorizado/2.0`.
- P1: `refactorizado/1.1` y `refactorizado/2.1`.
- P2: `1.2-dm-p2-exploracion-riesgo` y `2.2-dm-p2-refactorizacion`.

Los `2.0`, `1.1` y `2.1` que están directo en `notebooks/` son la versión anterior, con rezagos, y se conservan como historial.

## Instalación

Requiere Python 3.11.9 y Git.

```bash
git clone https://github.com/makroem/TC5061-Proyecto-Equipo39.git
cd TC5061-Proyecto-Equipo39
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install --no-deps -e .
.venv/bin/python -m pip check
```

En Windows usa `py -3.11 -m venv .venv` y `.venv\Scripts\python.exe`. Si no tienes 3.11.9, `uv python install 3.11.9` lo instala.

## Ejecución

```bash
python -m mibici_equipo39.dataset --verify-manifest
python -m mibici_equipo39.features
python -m mibici_equipo39.modeling.train --question all --member personaN
python -m pytest tests -q
```

1. La ingesta descarga unos 390 MB y verifica los hashes; `--freeze-manifest` solo se usa para una versión nueva de datos aprobada por PR.
2. `features` construye las tablas en `data/processed` y verifica la partición.
3. `train` registra baseline y candidato de cada pregunta en el experimento `mibici-equipo39`. Pide un árbol de Git limpio para que cada run quede ligado a su commit.

Con MLflow Projects (detalle en `references/ejecucion_mlproject.md`):

```bash
mlflow run . -e main --env-manager local --experiment-name mibici-equipo39 --run-name main-personaN -P member=personaN
python -m mlflow ui --backend-store-uri sqlite:///mlflow.db --host 127.0.0.1 --port 5000
```

También existen `make data`, `make features`, `make train MEMBER=personaN` y `make test`.

## Modelos

| | Baseline | Candidato | Selección |
|---|---|---|---|
| P1 | Media de train por estación, día y hora | `TargetEncoder` de estación + `HistGradientBoostingRegressor` Poisson | Menor `val_mae`; hoy gana el baseline |
| P2 | `DummyClassifier(prior)` por riesgo | One-hot de `station_id`, calendario escalado y `LogisticRegression` liblinear balanceada | Mayor `val_macro_f1`; umbral en rejilla 0.05-0.95 con recall >= 0.80 |
| P3 | KMeans, k=3 | GaussianMixture, 3 componentes | En desarrollo (persona4) |

Cada run registra rango de fechas, `data_version`, `split_id`, semilla, hiperparámetros, métricas con prefijo `train_`/`val_`/`test_`, y etiquetas de equipo, pregunta y commit. Prueba se evalúa una sola vez.

## Flujo de trabajo con Git

- `main` está protegida: todo entra por Pull Request con una aprobación y se mergea con merge commit para conservar la autoría.
- Ramas `tipo/personaN-descripcion` (por ejemplo `feat/persona3-riesgo-p2`) y commits con Conventional Commits: `feat`, `fix`, `docs`, `test`, `chore`.
- Cada integrante abre al menos un PR y revisa el de otro.
- El historial anterior de la ingesta está en `references/README_anterior_persona1.md` y `references/colaboracion.md`.

## Integrantes

| Persona | Integrante | GitHub | Rol |
|---|---|---|---|
| persona1 | Marco | makroem | Estructura, configuración, ingesta y manifiesto |
| persona2 | Stefania | a01236059-lab | Exploración, variables, partición, P1 y ML Canvas |
| persona3 | Diego Martínez | Sanciprian | Etiquetas y modelo de P2, pruebas y MLproject |
| persona4 | Diego Hurtado | diegoHurtado01 | P3, arquitectura, README final y propuesta |
