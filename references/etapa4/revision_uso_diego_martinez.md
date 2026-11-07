# Revisión de uso y respuestas HTTP de la API P1

Tarea #48. Revisó Diego Martinez el 6 de noviembre de 2026, sobre `main` en `27e8c0e`. Se revisaron
las instrucciones de servicio del README, el [contrato](contrato_api.md) y el código de
`mibici_equipo39/serving/app.py` y `schemas.py`.

## Rutas y códigos

| Ruta | Para qué sirve | Códigos esperados |
|---|---|---|
| `GET /health` | Saber si el proceso responde. No depende del modelo. | 200 `{"status": "ok"}`, también si el modelo no cargó. |
| `GET /ready` | Saber si el modelo cargó y cuál es. El healthcheck del contenedor usa esta ruta. | 200 con `model_name`, `model_version` y `model_bundle_sha256`. 503 si el modelo no cargó. |
| `POST /predict` | Pedir entre 1 y 100 predicciones de salidas por estación y hora. | 200 con las predicciones en el orden pedido. 422, 503 o 500, según la tabla siguiente. |
| `GET /docs` | Probar el contrato desde el navegador. `/openapi.json` tiene la definición. | 200, también si el modelo no cargó. |

En `/predict` cada error de cliente o de servidor tiene su propio código:

| Código | Quién falla | Cuándo | Cuerpo |
|---|---|---|---|
| 422 | La solicitud | Tipo o rango incorrecto, calendario incoherente, campo faltante o extra, lista vacía o de más de 100, JSON mal formado o sin `Content-Type: application/json`. | `detail` con `loc`, `msg` y `type`; no devuelve el valor enviado. |
| 503 | El servicio, antes de predecir | El modelo no cargó al iniciar. Se corrige revisando el paquete y reiniciando; repetir la solicitud no ayuda. | `{"detail": "Modelo no disponible."}` |
| 500 | El modelo, al predecir | El modelo lanzó un error o dio una salida negativa, no finita o de otro tamaño. | `{"detail": "No se pudo completar la prediccion."}`, sin traza ni rutas. |

La solicitud se valida antes de revisar el modelo. Por eso una solicitud inválida recibe 422 aunque
el servicio no esté preparado, y 503 solo aparece con una solicitud válida. Fuera del contrato,
FastAPI responde 405 a otro método en una ruta existente (por ejemplo `GET /predict`) y 404 a una
ruta inexistente.

## Qué se ejecutó y qué solo se revisó

En macOS ARM, Python 3.11.9, con un entorno nuevo instalado desde `requirements-api-dev.txt`
(`pip check` sin problemas). No había paquete del modelo en esta máquina.

- `pytest tests/api --confcutdir=tests/api`: 76 aprobadas.
- Uvicorn local sin modelo y solicitudes con `curl`: `/health` 200, `/ready` 503, `/docs` 200,
  `/openapi.json` 200; `/predict` con el ejemplo versionado 503, con lista vacía 422 y sin
  `Content-Type` 422.
- `TestClient` con un modelo simulado para los casos que necesitan un modelo cargado: 200 en
  `/ready` y `/predict`, los 422 de la tabla, 500 cuando el modelo lanza un error o devuelve un
  valor negativo o NaN, 405 y 404.

Solo se revisó, sin ejecutarlo: la construcción y el healthcheck del contenedor, los comandos de
PowerShell y la respuesta con el modelo real. Los respaldan el
[registro de implementación](../../reports/etapa4/cierre_api_marco_20261103.md) y la revisión de
Diego Hurtado en el PR #49.

## Observaciones sobre las instrucciones

1. La tabla de rutas del README no decía que la validación va primero ni que el 422 también cubre
   JSON mal formado o falta de `Content-Type`. Esto último importa con `curl`, que sin el encabezado
   envía el cuerpo como formulario.
2. Después de `docker inspect` no se decía qué resultado esperar. Con el Containerfile actual el
   estado es `starting` y pasa a `healthy` en la primera comprobación de `/ready`, unos 30 segundos
   después. `unhealthy` indica que `/ready` no responde 200; la causa queda en `docker logs`.
3. Swagger UI se descarga de `cdn.jsdelivr.net`. Sin internet `/docs` se ve en blanco aunque el
   servicio funcione; `/openapi.json` sí se sirve localmente.
4. Los comandos de servicio solo están en PowerShell. Falta el equivalente para macOS y Linux.
5. El contrato decía "200 con el linaje" en `/ready` sin nombrar los campos.

Las cinco se corrigen con cambios de redacción en el README y en el contrato. No cambian el
servicio, los modelos, el Registry ni los resultados ya publicados.
