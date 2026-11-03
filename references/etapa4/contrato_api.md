# Contrato de la API P1 — Etapa 4

Actualización: 3 de noviembre de 2026. Implementación: Marco. Revisión independiente: Diego Hurtado.

## Modelo y alcance

Se sirve P1, demanda esperada de viajes por estación en la hora objetivo. El modelo aprobado es `mibici-equipo39-p1-demanda`, versión **1**, run `66414a8b45164d3a8f5b9f42e7cb387b`, variante baseline. El manifiesto [model_manifest.json](model_manifest.json) conserva el nombre, versión, commit de entrenamiento, versión de datos y las 22 huellas.

Se descarga la versión numérica del Registry antes de construir y se incluye el paquete completo en la imagen. La inferencia no necesita acceder al Registry ni a los CSV. No se vuelve a entrenar, no se cambia el alias y se conserva la partición temporal del modelo vigente. Los hashes verifican integridad contra el manifiesto revisado; el paquete serializado debe provenir del almacén de confianza del equipo.

## Solicitud y validación

`POST /predict` recibe `{"instances": [...]}`, con entre 1 y 100 filas. Se implementó con Pydantic estricto: no convierte cadenas en enteros ni acepta booleanos como números, valores no finitos, campos adicionales o calendario incoherente.

| Campo | Tipo tabular | Regla |
|---|---|---|
| station_id | object/string | Texto de 1 a 6 dígitos, sin ceros iniciales. |
| hour_of_day | int32 | De 0 a 23. |
| day_of_week | int32 | De 0 a 6, lunes = 0. |
| month | int32 | De 1 a 12. |
| is_weekend | int64 | 1 si el día es 5 o 6; en otro caso 0. |
| hour_sin / hour_cos | float64 | seno/coseno de 2π × hora / 24. |
| month_sin / month_cos | float64 | seno/coseno de 2π × mes / 12. |

Los valores cíclicos usan tolerancia absoluta de `1e-6`. La API acepta identificadores numéricos desconocidos: el baseline aplica su media global cuando no encuentra la estación. Esto conserva el comportamiento registrado y no acredita una estimación específica para una estación nueva; debe considerarse una respuesta de respaldo. Los ejemplos son artificiales y no contienen datos de usuarios.

La respuesta contiene `model_name`, `model_version`, `model_bundle_sha256` y `predictions`. Cada predicción conserva `station_id` y `predicted_trips` en el orden solicitado. Se devuelven valores decimales sin redondearlos; salidas negativas, no finitas o de tamaño incorrecto provocan un error controlado.

## Servicio y errores

- `GET /health`: 200 cuando el proceso responde.
- `GET /ready`: 200 con el linaje cuando el modelo se cargó; 503 si falló su preparación.
- `POST /predict`: 200 con las predicciones, 422 para solicitudes inválidas, 503 si no está preparado y 500 para un fallo de inferencia.
- `GET /docs`: contrato interactivo; `/openapi.json` publica su definición.

La carga verifica inventario, firma y corrida antes de deserializar, y ocurre una vez por proceso durante el inicio de FastAPI. El cliente no puede elegir rutas, modelos, URI ni versiones. Las respuestas de error no incluyen trazas, rutas internas ni el cuerpo original. Un fallo al cargar deja `/health` disponible y `/ready` en 503 para que el operador pueda diagnosticarlo y reiniciar después de corregirlo.

`MODEL_DIR` usa `models/serving/p1` localmente y `/app/model` en la imagen. `MODEL_MANIFEST` indica el JSON aprobado. Ejecutar con `python -B` evita alterar el paquete con bytecode. El contenedor escucha en 8000 y se publica solo en la interfaz local del equipo.

## Responsables y continuidad

La [distribución vigente](distribucion_actual.md) sustituye las asignaciones iniciales: Marco completa esquemas, adaptador, API y preparación del contenedor; Diego Hurtado revisa y repite la validación de despliegue. Stefania y Diego Martinez realizan revisiones acotadas de ejemplos y documentación. Sus tareas no son dependencias técnicas para la implementación y pueden ser cubiertas por Marco o Diego Hurtado conservando la autoría real.

La captura original del Registry y los manifiestos conservan su contenido. Las pruebas HTTP locales y las pruebas desde el contenedor se documentan por separado; no se presentan como equivalentes.
