# Calidad de datos con DeepChecks: motor, política y primera validación real

Aporte de Diego Martinez a la Etapa 3. Implementa la interfaz de
[contrato_calidad.md](../../references/etapa3/contrato_calidad.md): motor en
`mibici_equipo39/validation/data_checks.py` y política en
[quality_policy.json](../../references/etapa3/quality_policy.json).

## Cómo se ejecuta

En el entorno separado de DeepChecks, desde la raíz del repositorio:

```bash
.venv-deepchecks/bin/python -m mibici_equipo39.validation.data_checks --question all --stage development
```

En Windows usar `.venv-deepchecks/Scripts/python.exe`. El resumen y el HTML de DeepChecks quedan en
`private_quality/data_checks/<etapa>/`, fuera de Git. `--stage final` agrega prueba y solo corre
con la política congelada (`"frozen": true`); con la política en borrador termina con código 2.

| Salida | Significado |
|---|---|
| 0 | Obligatorias completas, sin fallos críticos |
| 1 | Fallo crítico de datos |
| 2 | Error de ejecución u obligatoria sin evaluar |

Si DeepChecks no se puede importar (por ejemplo, en el entorno del proyecto con NumPy 2), sus
comprobaciones quedan NOT_EVALUATED con la causa y la salida es 2. Nunca cuentan como aprobadas.

## Qué revisa

**Linaje (todas las preguntas).** La data_version de las tablas coincide con los dos manifiestos.
metadata, X, y_p1 y y_p2 tienen las mismas filas. Cada fila cae en el conjunto que fija
`split_manifest.json`, sin recalcular la partición. Los 151 Parquet de `data_manifest.json` coinciden
en filas y hash lógico.

**Integridad (pandas, datos completos).** Columnas de X exactas, sin nulos, llave estación-hora única,
dominios del calendario y de los objetivos, malla completa estación por hora, mínimos de estaciones
y de positivos. Para P2 también se recalcula la etiqueta con `proxy_labels`. Para P3, cada bloque de
24 horas del perfil suma uno.

**DeepChecks (muestra de 100,000 filas por conjunto, semilla 39).** Variable constante, tipos
mezclados, correlación con el objetivo (PPS), mezcla de muestras entre train y el otro conjunto,
deriva de variables, deriva del objetivo de P1 y estaciones nuevas.

Cada regla tiene severidad: `critical` produce FAIL y `warning` produce WARN. La deriva siempre es
`warning`, porque la partición es cronológica y un cambio de temporada no prueba un defecto. Los
meses se excluyen de la deriva porque la partición los separa por diseño.

## Resultados en desarrollo

Corrida del 30 de octubre de 2026 en macOS sobre los datos locales (`e9de13df`, split `ab6301f9`),
entorno `.venv-deepchecks` con DeepChecks 0.19.1 y NumPy 1.26.4. Tardó unos 32 segundos.

| Resultado | Comprobaciones |
|---|---|
| PASS | 64 |
| WARN | 2 |
| FAIL | 1 |
| NOT_EVALUATED | 0 |

- **P1:** 369 estaciones elegibles, 2,152,008 filas en train y 540,216 en validación, malla
  completa, sin nulos ni duplicados. Deriva máxima de variables 0.02 (day_of_week) y del objetivo
  0.005 (KS).
- **P2:** 469 estaciones, 11,072 y 14,114 positivos en train (bicicletas y anclajes) y 2,213 y 2,926
  en validación. Las etiquetas recalculadas coinciden en todas las filas. La prevalencia de validación
  es 0.80 y 0.83 veces la de train.
- **P3:** 369 perfiles por conjunto, todos normalizados. WARN: 6 columnas de madrugada (2 a 4 h)
  valen cero en todas las estaciones en train y 1 en validación. No invalida el perfil, pero esas
  columnas no ayudan a separar grupos. La deriva de perfiles queda bajo 0.2 en 46 de 48 horas; la
  mayor es 0.29 a las 5 h de fin de semana.
- **FAIL de linaje:** `processed/stations.parquet` tiene las 484 filas esperadas, pero su hash lógico
  no coincide con el manifiesto. Los otros 150 archivos sí coinciden.

## Hallazgos

1. **Hash de estaciones distinto en macOS.** El CSV de origen tiene el SHA256 del manifiesto y
   `clean_stations` produce exactamente el mismo Parquet que el local, pero `logical_hash` da otro
   valor, con pandas 2.2.3 en ambos entornos. La ingesta oficial de Marco corrió con
   `--verify-manifest` en Windows y terminó bien, así que el hash parece depender de la plataforma.
   En macOS, `--verify-manifest` fallaría por este archivo. Hay 11 nombres de estación con espacios
   al inicio o al final, que son el primer candidato. Responsable de confirmarlo: Marco, con una
   comparación por columna en su equipo.
2. **`requirements-deepchecks.txt` no fijaba `setuptools`.** DeepChecks importa `pkg_resources`.
   Con `python -m venv` en 3.11 se instala setuptools 65.5.0 por defecto, pero con otras herramientas
   el entorno queda roto. Se fija 65.5.0, la versión incluida en Python 3.11.9, junto con loguru y typer para
   que el motor use `features.py` en lugar de copiar sus reglas. Las versiones son las de
   `requirements.txt`.
3. **LabelDrift no sirve para etiquetas raras.** Usa V de Cramér: una prevalencia diez veces mayor
   (0.4% a 4%) da 0.12 y pasa el umbral de 0.15. Para P2 se reemplaza por la razón de prevalencia
   contra train, con aviso fuera de 0.5 a 2 veces.
4. **Bandit:** tres avisos bajos (B404, B603) por la llamada a Git del motor. Usa lista de argumentos,
   Git resuelto con `shutil.which`, sin shell ni entrada del usuario, igual que `tracking.py`.

## Pruebas

- `tests/test_data_checks.py` (16): datos limpios, seis daños críticos con salida 1, partición y
  data_version alteradas, DeepChecks no disponible con salida 2, avisos que no cambian la salida,
  etapa final con política congelada, tabla faltante y, si existe `.venv-deepchecks`, la corrida real
  de DeepChecks con un control positivo y uno negativo (variable constante).
- `tests/test_stage3_p2.py` (8): límites inclusivos de la etiqueta, alerta en el umbral exacto,
  entrada vacía, train con una sola clase, validación sin positivos, probabilidades en [0, 1], tipos
  inválidos y reproducción sin calibración congelada.
- `tests/test_stage3_registro.py` (14): cada problema de linaje bloquea el registro, la reproducción
  debe ser de la variante seleccionada, comparación de la predicción al cargar y la llamada a Git sin
  shell que rechaza salidas que no son un commit.

Suite completa combinada con main (MLflow 3.17.2 y PyArrow 23.0.1): 211 pruebas aprobadas.

## Pendiente

- Stefania y Diego Hurtado confirman los criterios de P1 y P3 en la política. Después se congela
  (`"frozen": true`) y se corre `--stage final` una sola vez.
- Resolver el hash de estaciones antes de la corrida final; no se cambia la política para que pase.
