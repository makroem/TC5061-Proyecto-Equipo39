# Contrato inicial de la API — Etapa 4

Responsable del arranque: Marco. Fecha: 2 de noviembre de 2026.
Base integrada: `5344be3498bd3d46459c7e905e341fd6f5aec0c2`.

## Modelo y alcance

Se empaqueta P1, demanda esperada de viajes por estación en la hora objetivo. El Registry oficial resolvió `mibici-equipo39-p1-demanda@champion` a la versión **1**, run `66414a8b45164d3a8f5b9f42e7cb387b`, variante `baseline` (media estacional). No se vuelve a entrenar ni se modifica el alias. Nombre, versión, commit de entrenamiento, versión de datos y las 22 huellas están en [model_manifest.json](model_manifest.json).

La opción elegida es descargar el paquete completo del Registry y copiarlo a la imagen. La descarga necesita acceso al almacén oficial; la inferencia usa únicamente el paquete local. Los hashes detectan cambios respecto al manifiesto aprobado; no certifican la seguridad de un modelo obtenido de una fuente desconocida. El manifiesto y el código se revisan mediante PR.

El código integrado usa doce meses y partición temporal (`chronological_holdout`). Se conserva esta configuración. La mención a partición aleatoria en el manual inicial no describe el modelo vigente; esta etapa no modifica datos ni particiones.

## Interfaz para los otros módulos

- `Settings.from_env()` entrega `model_dir` y `model_manifest` como `Path`.
- `load_model(model_dir, manifest_path)` devuelve un `LoadedModel` con `model`, `manifest` y `predict(frame)`.
- La carga valida inventario, firma y run antes de deserializar. Cargar una sola vez en el ciclo de inicio de FastAPI.
- `MODEL_DIR` apunta localmente a `models/serving/p1`; en el contenedor debe ser `/app/model`.
- `MODEL_MANIFEST` apunta al JSON versionado, copiado a una ruta conocida dentro de la imagen.
- Usar `python -B` o `PYTHONDONTWRITEBYTECODE=1` para evitar que el código incluido en el modelo cree archivos nuevos dentro del paquete verificado.
- El consumidor HTTP no puede proporcionar rutas, nombres de modelo, URI ni versiones arbitrarias.

## Firma observada de P1

La solicitud propuesta es `{"instances": [...]}`, con 1 a 100 filas. Stefania implementa los esquemas y confirma sus reglas en un PR; este documento establece el acuerdo inicial, no afirma que la API exista.

| Campo | Tipo tabular exigido | Regla propuesta |
|---|---|---|
| station_id | string/object | Texto no vacío. Mantener el identificador como texto. |
| hour_of_day | int32 | Entero de 0 a 23. |
| day_of_week | int32 | Entero de 0 a 6; lunes = 0. |
| month | int32 | Entero de 1 a 12. |
| is_weekend | int64 | 0 o 1; coherente con el día. |
| hour_sin | float64 | seno(2π × hora / 24). |
| hour_cos | float64 | coseno(2π × hora / 24). |
| month_sin | float64 | seno(2π × mes / 12). |
| month_cos | float64 | coseno(2π × mes / 12). |

Rechazar valores no finitos, campos extra y entradas inconsistentes. Documentar tolerancia numérica para los campos cíclicos. El baseline tiene respaldo por estación/hora y luego media global; Stefania debe decidir y probar el tratamiento público de una estación no conocida. La comprobación técnica de Marco incluye una estación artificial no conocida, sin convertirla en recomendación de uso.

La respuesta propuesta contiene `model_name`, `model_version`, `model_bundle_sha256` y `predictions`. Cada predicción conserva `station_id` y `predicted_trips`, en el orden de entrada. La salida representa demanda esperada, puede ser decimal y no se redondea para las pruebas de paridad.

## Endpoints a implementar por Diego Martinez

- `GET /health`: proceso disponible.
- `GET /ready`: modelo verificado y cargado; 503 si no está preparado.
- `POST /predict`: inferencia validada; 422 para solicitudes inválidas.
- `GET /docs`: contrato interactivo.

No exponer trazas internas al cliente. El proceso escucha `0.0.0.0:8000` dentro del contenedor; el motor publica `127.0.0.1:8000:8000` en la computadora.

## Entregas y dependencias

| Responsable | Puede comenzar ahora | Necesita para cerrar |
|---|---|---|
| Marco | Exportador, cargador, manifiesto, dependencias, seguridad y revisión de contrato. | API, esquemas y contenedor integrados para verificar un clon limpio. |
| Stefania | `schemas.py`, `predictor.py`, ejemplos y pruebas usando esta firma. | Revisar el manifiesto y contrastar sus casos con el modelo oficial. |
| Diego Martinez | `app.py`, errores HTTP y pruebas con cargador controlado. | Esquemas/adaptador de Stefania y cargador de Marco para inferencia real. |
| Diego Hurtado | Revisar el PR de Marco, preparar motor y Containerfile. | API y esquemas para probar el contenedor; debe validar estas dependencias también en Linux. |

El primer ensayo Linux puede usar ramas de trabajo identificadas antes del merge. No se necesita esperar a que toda la solución esté integrada para detectar incompatibilidades. El cierre desde clon limpio sí se hace sobre `main` con los PR aprobados.

## Archivos y exclusiones

Versionar código de `mibici_equipo39/serving/`, `tests/api/`, requisitos, este contrato, manifiesto y resúmenes/capturas revisados. `models/serving/p1`, entornos, bases de MLflow, datos, credenciales y salidas privadas permanecen excluidos. Las reglas actuales de `.gitignore` ya lo cubren; se verificaron sin reemplazar el archivo.

Diego Hurtado debe permitir el paquete P1 en el contexto de construcción aunque Git lo ignore. `.containerignore` y `.dockerignore` no deben excluir por accidente el modelo que se copiará. Usar copias explícitas, usuario sin privilegios y no incorporar la base de MLflow ni credenciales a la imagen.

## Criterio de cierre

Este arranque no acredita una API ni un contenedor funcionando. Falta la validación HTTP, Linux, captura de predicción real y reproducción final. Los responsables deben conservar una revisión real de otro integrante y registrar evidencia de sus pruebas.
