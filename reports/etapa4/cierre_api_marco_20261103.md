# Implementación y validación del servicio P1

Fecha: 3 de noviembre de 2026. Implementación y ejecución: Marco. Revisión independiente pendiente: Diego Hurtado.

## Cambio y continuidad

Marco completó esquemas Pydantic, conversión de tipos, API FastAPI, manejo de errores, pruebas y Containerfile. La implementación ya no espera módulos de Stefania o Diego Martinez. La [distribución vigente](../../references/etapa4/distribucion_actual.md) registra sus revisiones acotadas y las personas que pueden cubrirlas.

El servicio conserva el paquete aprobado de P1, versión 1 y run `66414a8b45164d3a8f5b9f42e7cb387b`. No se entrenó, recalibró ni modificó un alias. El hash del paquete es `dedce1eb08bda971a42fba311224c88e56f75cd2789dbb391e9445951931bd80`.

## Pruebas de código y servicio local

- Suite `tests/api`, aislada mediante `--confcutdir=tests/api`: **69 pruebas aprobadas**, 0 fallos, 1 advertencia, 2.45 s. Incluye 31 pruebas previas y 38 del contrato, adaptador y HTTP.
- `pip check`: sin dependencias incompatibles en el entorno de servicio Windows.
- Bandit del módulo de servicio: 1 aviso LOW B404 en la importación preexistente de subprocess del verificador independiente, 0 MEDIUM y 0 HIGH. Los módulos nuevos no añadieron hallazgos.
- Servicio Windows por HTTP en 18039: 72 casos, diferencia máxima 0.0 contra una carga independiente del paquete local; repetición idéntica y rechazo 422. [Resultado local](verificacion_http_marco_20261103.json).

El verificador HTTP se corrigió durante la preparación para no depender del generador de entradas del PR #45, que en ese momento estaba pendiente. La comprobación válida es la que terminó y produjo el JSON enlazado. Al probar Swagger se detectó que el ejemplo generado automáticamente no respetaba los campos cíclicos; se añadió un ejemplo válido y se comprobó mediante una prueba de OpenAPI. El contrato de errores documenta las respuestas reales, sin reflejar el cuerpo recibido.

La advertencia de Starlette indica la futura sustitución de httpx en TestClient. No afecta al resultado de esta suite. MLflow también advierte diferencias entre las dependencias históricas del modelo y el entorno reducido; no se modificó el archivo de dependencias incluido en el modelo para ocultarlas. La paridad comprobada cubre los casos indicados y no demuestra equivalencia para cualquier entrada ni exactitud predictiva frente a viajes reales.

## Comprobación en contenedor Linux

La construcción final terminó correctamente con Docker 29.9.2 y el código de servicio del commit `73204ca`. La imagen resultante es `sha256:69cc6de014e04336aa5e39da7253a2e209739441a228e1275d581045c2498242`.

El contenedor ejecutó Linux amd64 con usuario `10001:10001`, sistema de archivos de solo lectura, eliminación de capacidades y `no-new-privileges`. El puerto 8000 se publicó únicamente en `127.0.0.1:18040`. Docker informó `running` y `healthy`. Estos valores provienen de la inspección del contenedor y se guardan en [estado_contenedor_20261103.json](estado_contenedor_20261103.json).

La prueba HTTP contra esa imagen aprobó **72 casos**, sin diferencia respecto de las predicciones de una carga independiente del paquete en Windows: diferencia absoluta máxima **0.0**. Las respuestas repetidas fueron idénticas, `/health`, `/ready` y `/docs` devolvieron 200, y las dos solicitudes inválidas devolvieron 422. La huella del modelo se conservó. [Resultado del contenedor](verificacion_contenedor_marco_20261103.json).

En Swagger se ejecutó el ejemplo incluido en OpenAPI. La API respondió 200 y `predicted_trips=1.6764705882352942`, con el nombre, versión y huella esperados. Las siguientes capturas son originales del navegador, sin editar:

- [Respuesta 200 y linaje](evidence/E03_api_contenedor_respuesta_200.jpg).
- [Página completa con solicitud, respuesta y esquemas](evidence/E04_api_contenedor_pagina_completa.jpg).
- [Huellas y procedencia de las capturas](capturas_api_20261103.json).

![Respuesta real del contenedor](evidence/E03_api_contenedor_respuesta_200.jpg)

El JSON de [respuesta del ejemplo](../../references/etapa4/examples/predict_response.json) contiene la misma salida observada. La inspección del contenedor y la prueba HTTP se complementan: la comparación por sí sola no prueba que el servicio corra en Docker. No se afirma haber ejecutado una auditoría de vulnerabilidades de la imagen base ni una prueba de carga.

## Reproducción y alcance

El README contiene exportación del modelo, instalación, construcción, ejecución y consumo. Los ejemplos son artificiales. `verify_http` compara las predicciones de la API con el paquete local aprobado y verifica integridad después de cargarlo. Las huellas de los archivos del modelo y el manifiesto original permanecen intactas.

Se permite la estación desconocida como respuesta de respaldo del baseline (media global); no se interpreta como una estimación aprendida para esa estación. El servicio está publicado solo en localhost, no tiene una prueba de carga ni un despliegue público autenticado.

El catálogo histórico no es necesario para atender predicciones: la imagen usa el modelo empaquetado. Su recuperación automática ya está integrada en `main` mediante el [PR #46](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/46), aprobado por Diego Hurtado. El respaldo de Google Drive conserva la huella del catálogo original.

La revisión de Diego Hurtado y la integración del [PR #49](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49) siguen pendientes. Los PR #45 y #46 ya fueron aprobados e integrados. El cierre completo del servicio sobre `main` se realizará después de integrar el PR #49.

## Comprobación tras integrar catálogo y paridad

Actualización del 3 de noviembre de 2026, hora de Ciudad de México. Marco integró los PR #45 y #46 con sus aprobaciones vigentes, sin omitir protecciones ni eliminar ramas. `main` quedó en `3c38b435269204729297342fc2f0013f6be455bb`. Después incorporó ese commit a la rama de la API (`9832745`), conservando en el README tanto las instrucciones del servicio como la recuperación del catálogo.

| Comprobación | Resultado | Código comprobado |
|---|---|---|
| Suite de API, incluidos los siete casos del perfil ampliado | 76 aprobadas, 0 fallos, 1 advertencia de Starlette; 1.99 s | Rama de API, commit `9832745` |
| Descarga, datos, calidad de ingesta y manifiesto de estaciones | 51 aprobadas, 0 fallos, 14 advertencias de Pyparsing; 28.89 s | Copia limpia de `main`, commit `3c38b43` |
| Recuperación real del catálogo sin copia previa ni caché configurada | `verified_backup`, 484 filas, 40,841 bytes; SHA256 coincidente | Misma copia limpia de `main`, sin sesión de Google |

La huella descargada fue `206e45fe633922b634d858142fa21e6fd9f4c421b6435c02980ef290cc2df90d`. Se reutilizaron los entornos de Python existentes; no se afirma haber instalado todas las dependencias desde cero, descargado de nuevo doce meses de viajes ni repetido entrenamientos. El contenedor y las capturas anteriores siguen acreditando la construcción de servicio `73204ca`, no una nueva imagen de `9832745`. La siguiente comprobación sobre el servicio integrado depende únicamente de la revisión y aprobación del PR #49.
