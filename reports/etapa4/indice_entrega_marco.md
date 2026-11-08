# Índice de entrega — Etapa 4, Equipo 39

Revisión documental: 8 de noviembre de 2026, hora de Ciudad de México. Responsable: Marco. Repositorio: [TC5061-Proyecto-Equipo39](https://github.com/makroem/TC5061-Proyecto-Equipo39).

## Estado y alcance

Los archivos técnicos y las evidencias enumerados abajo ya están publicados en `main`, verificados sobre `3bfe6c0d3623ae965f7242901732c62b4b6f8675`. Este índice y la actualización del estado de participación se incorporan mediante un PR documental con revisión independiente. No son una nueva ejecución del servicio.

La entrega utiliza **Docker**, opción admitida expresamente junto con Podman en las instrucciones. Se conserva el nombre `Containerfile`. No se afirma haber ejecutado la imagen con Podman.

El modelo es `mibici-equipo39-p1-demanda`, versión **1**, correspondiente al alias `champion` verificado al preparar la entrega. El servicio fija esa versión y comprueba las huellas de sus 22 archivos. El modelo se descarga desde el Registry antes de construir la imagen y queda incluido en ella; las peticiones no dependen de que el servidor de MLflow esté encendido.

La ejecución final registrada es del **4 de noviembre de 2026**, sobre `b1ddc47a0234def92b23c5ae7d6804f05e34697f`: 76 pruebas de API aprobadas, instalación desde un clon y un entorno nuevos, imagen Linux construida y 72 casos HTTP con diferencia máxima 0.0 frente al paquete original. Las capturas y JSON están integrados mediante el PR #50. La comparación con `3bfe6c0` no presenta cambios en el código de servicio, sus pruebas, dependencias, Containerfile, exclusiones de construcción, configuración central ni manifiesto del modelo.

## Actividades de Marco y evidencia de cierre

| Actividad de la entrega | Resultado verificable | Estado |
|---|---|---|
| Recuperar el modelo del Registry por nombre y versión | Exportación de P1 v1, firma, corrida de origen, versión de datos y 22 huellas en el manifiesto; captura E02 | Completada e integrada |
| Integrar el modelo con FastAPI | `POST /predict`, carga al inicio, adaptador y respuestas JSON con linaje | Completada e integrada, PR #49 |
| Validar entradas y salidas | Esquemas Pydantic, límites de calendario, coherencia de campos cíclicos, lotes de 1 a 100 filas y predicciones finitas no negativas | Completada e integrada; cubierta por la suite de API |
| Empaquetar el servicio | Containerfile, dependencias fijadas, exclusiones de construcción, usuario no privilegiado y comprobación de salud | Completada; construcción Docker documentada |
| Probar el contenedor real | 72 casos HTTP, repetición idéntica, diferencia máxima 0.0 y rechazo 422 para entradas inválidas | Completada; registros y capturas finales publicados |
| Documentar construcción, ejecución y uso | README con comandos, solicitud, respuesta, recuperación del paquete y justificación de inferencia síncrona | Completada e integrada |
| Conservar pruebas, seguridad y etapas anteriores | Suite de API independiente; escaneos de servicio documentados; modelo, datos y bases fuera de Git | Completada dentro del alcance registrado |
| Abrir cambios y obtener revisión independiente | PR #45, #46, #49 y #50 revisados por Diego Hurtado e integrados | Completada |
| Revisar aportaciones de otros integrantes | Marco revisó e integró el PR #55 de Stefania y el PR #58 de Diego Martinez | Completada; tareas #47 y #48 cerradas |

No quedan tareas técnicas de Marco pendientes según este contraste. La revisión de una actualización documental nueva corresponde a otra persona; no se sustituye con una aprobación propia. No se ha verificado el envío en Canvas en esta revisión.

## Archivos de implementación, entorno y pruebas

Los enlaces de archivo son relativos a la raíz del repositorio y funcionan desde este documento en GitHub. El alcance es la Etapa 4, no el inventario completo de las entregas anteriores. Los archivos de configuración compartida conservan las aportaciones de otras etapas.

| Ruta en el repositorio | Función |
|---|---|
| [README.md](../../README.md) | Instalación, modelo, construcción, ejecución, consumo y evidencias |
| [Containerfile](../../Containerfile) | Imagen OCI con aplicación, dependencias y modelo verificado |
| [requirements-api.txt](../../requirements-api.txt) | Dependencias fijadas del servicio |
| [requirements-api-dev.txt](../../requirements-api-dev.txt) | Dependencias de pruebas y revisión del servicio |
| [.dockerignore](../../.dockerignore) | Exclusiones y archivos permitidos en la construcción Docker |
| [.containerignore](../../.containerignore) | Exclusiones equivalentes para Podman |
| [.gitignore](../../.gitignore) | Exclusión de modelos, datos, entornos y almacenes privados |
| [mibici_equipo39/serving/__init__.py](../../mibici_equipo39/serving/__init__.py) | Módulo de servicio |
| [mibici_equipo39/serving/export_model.py](../../mibici_equipo39/serving/export_model.py) | Recuperación de la versión aprobada y comprobación de linaje |
| [mibici_equipo39/serving/model_loader.py](../../mibici_equipo39/serving/model_loader.py) | Integridad y carga local del paquete |
| [mibici_equipo39/serving/settings.py](../../mibici_equipo39/serving/settings.py) | Rutas y límites de despliegue |
| [mibici_equipo39/serving/schemas.py](../../mibici_equipo39/serving/schemas.py) | Validación de entradas, salidas y errores |
| [mibici_equipo39/serving/predictor.py](../../mibici_equipo39/serving/predictor.py) | Conversión de entradas y predicción |
| [mibici_equipo39/serving/app.py](../../mibici_equipo39/serving/app.py) | FastAPI, ciclo de vida y endpoints |
| [mibici_equipo39/serving/verify_model.py](../../mibici_equipo39/serving/verify_model.py) | Paridad entre Registry y paquete exportado |
| [mibici_equipo39/serving/verify_http.py](../../mibici_equipo39/serving/verify_http.py) | Comprobación real del servicio por HTTP |
| [tests/api/conftest.py](../../tests/api/conftest.py) | Preparación independiente de las pruebas de API |
| [tests/api/test_app.py](../../tests/api/test_app.py) | Contrato, validación y respuestas HTTP |
| [tests/api/test_export_model.py](../../tests/api/test_export_model.py) | Exportación e integridad de la selección |
| [tests/api/test_model_loader.py](../../tests/api/test_model_loader.py) | Rechazo de paquetes inválidos y carga |
| [tests/api/test_verify_model.py](../../tests/api/test_verify_model.py) | Verificador y perfil de comparación |

## Contrato y evidencias principales de Marco

| Ruta en el repositorio | Qué acredita |
|---|---|
| [references/etapa4/contrato_api.md](../../references/etapa4/contrato_api.md) | Contrato del servicio y criterios de aceptación |
| [references/etapa4/model_manifest.json](../../references/etapa4/model_manifest.json) | Modelo, versión, firma, linaje y huellas |
| [references/etapa4/examples/predict_request.json](../../references/etapa4/examples/predict_request.json) | Solicitud válida reproducible |
| [references/etapa4/examples/predict_response.json](../../references/etapa4/examples/predict_response.json) | Respuesta observada para el ejemplo |
| [references/etapa4/distribucion_actual.md](../../references/etapa4/distribucion_actual.md) | Responsables, revisiones y cierre de tareas |
| [reports/etapa4/cierre_api_marco_20261103.md](cierre_api_marco_20261103.md) | Implementación, comprobaciones y cierre final del 4 de noviembre; seguimiento documental del 8 |
| [reports/etapa4/verificacion_main_20261104.json](verificacion_main_20261104.json) | Clon y entorno nuevos, instalación y 76 pruebas aprobadas |
| [reports/etapa4/verificacion_http_main_20261104.json](verificacion_http_main_20261104.json) | 72 casos HTTP contra la imagen final |
| [reports/etapa4/estado_contenedor_main_20261104.json](estado_contenedor_main_20261104.json) | Imagen, salud, restricciones y puerto de la ejecución final |
| [reports/etapa4/capturas_api_main_20261104.json](capturas_api_main_20261104.json) | Procedencia y SHA256 de las dos capturas finales |
| [reports/etapa4/evidence/E05_api_main_respuesta_200.jpg](evidence/E05_api_main_respuesta_200.jpg) | Captura original de la respuesta 200 del contenedor final |
| [reports/etapa4/evidence/E06_api_main_pagina_completa.jpg](evidence/E06_api_main_pagina_completa.jpg) | Captura original de solicitud, respuesta y esquemas |
| [reports/etapa4/captura_registry_p1.md](captura_registry_p1.md) | Procedencia y huella de la captura del Registry |
| [reports/etapa4/evidence/E02_registry_p1.png](evidence/E02_registry_p1.png) | P1 versión 1, alias y linaje en MLflow |

Las capturas originales se conservan sin edición. Las marcas de tiempo UTC de E05 y E06 corresponden a la noche del 4 de noviembre en Ciudad de México. La interfaz de MLflow conserva sus nombres de producto y elementos originales.

## Registros complementarios e históricos

Estos archivos ya están publicados y permiten seguir el desarrollo. Las cifras de una ejecución anterior no reemplazan los 76 casos de la suite final ni los 72 casos HTTP. Los pendientes que aparecen en registros fechados se interpretan a la fecha de esos registros; el estado de tareas vigente se encuentra en la distribución actual.

| Ruta en el repositorio | Alcance |
|---|---|
| [reports/etapa4/arranque_marco.md](arranque_marco.md) | Preparación inicial del modelo y entorno |
| [reports/etapa4/verificacion_marco.json](verificacion_marco.json) | Resultado inicial y límites de esa fecha |
| [reports/etapa4/paridad_modelo_marco.json](paridad_modelo_marco.json) | Comparación básica con el Registry |
| [reports/etapa4/paridad_modelo_ampliada_marco.json](paridad_modelo_ampliada_marco.json) | 12,096 entradas artificiales, paridad en Windows |
| [reports/etapa4/validacion_ampliada_marco.json](validacion_ampliada_marco.json) | Validación del perfil ampliado |
| [reports/etapa4/seguimiento_marco_20261102.md](seguimiento_marco_20261102.md) | Seguimiento histórico de preparación y paridad |
| [reports/etapa4/seguridad_api.md](seguridad_api.md) | Interpretación de los chequeos iniciales de seguridad |
| [reports/etapa4/bandit_api.json](bandit_api.json) | Escaneo inicial de código del servicio |
| [reports/etapa4/bandit_servicio_20261103.json](bandit_servicio_20261103.json) | Escaneo posterior del servicio, un aviso LOW B404 documentado |
| [reports/etapa4/pip_audit_api.json](pip_audit_api.json) | Auditoría de dependencias de servicio en la fecha registrada |
| [reports/etapa4/pip_audit_api_dev.json](pip_audit_api_dev.json) | Auditoría del entorno de desarrollo en la fecha registrada |
| [reports/etapa4/verificacion_http_marco_20261103.json](verificacion_http_marco_20261103.json) | HTTP del servicio local en Windows |
| [reports/etapa4/verificacion_contenedor_marco_20261103.json](verificacion_contenedor_marco_20261103.json) | HTTP de la primera imagen Linux |
| [reports/etapa4/estado_contenedor_20261103.json](estado_contenedor_20261103.json) | Inspección de la primera imagen y su contenedor |
| [reports/etapa4/capturas_api_20261103.json](capturas_api_20261103.json) | Huellas de las capturas históricas E03 y E04 |
| [reports/etapa4/evidence/E03_api_contenedor_respuesta_200.jpg](evidence/E03_api_contenedor_respuesta_200.jpg) | Respuesta 200 de la primera imagen; puerto 18040 |
| [reports/etapa4/evidence/E04_api_contenedor_pagina_completa.jpg](evidence/E04_api_contenedor_pagina_completa.jpg) | Solicitud y respuesta de la primera imagen |

## Recuperación del catálogo: apoyo a la continuidad

Marco resolvió la disponibilidad del catálogo histórico mediante una copia con SHA256 verificado. Esta recuperación permite continuar la ingesta anterior; no es necesaria para responder predicciones con la imagen que ya contiene P1.

| Ruta en el repositorio | Función |
|---|---|
| [mibici_equipo39/config.py](../../mibici_equipo39/config.py) | Configuración compartida, rutas y respaldo |
| [mibici_equipo39/dataset.py](../../mibici_equipo39/dataset.py) | Recuperación y validación en la ingesta |
| [mibici_equipo39/prepare_catalog.py](../../mibici_equipo39/prepare_catalog.py) | Preparación del catálogo verificado |
| [references/stations_backup.json](../../references/stations_backup.json) | Fuente alternativa y huella de confianza |
| [tests/test_download.py](../../tests/test_download.py) | Pruebas de descarga y respaldo |
| [reports/etapa4/recuperacion_catalogo_20261103.md](recuperacion_catalogo_20261103.md) | Procedimiento y resultado de recuperación |
| [reports/etapa4/verificacion_respaldo_drive_20261103.json](verificacion_respaldo_drive_20261103.json) | Descarga comprobada y huella coincidente |
| [reports/etapa4/evidence/E05_catalogo_drive_detalle.jpg](evidence/E05_catalogo_drive_detalle.jpg) | Evidencia del respaldo del catálogo; distinta de E05 de la API |

## Revisiones de otros integrantes

| Archivo o revisión | Autor y aportación |
|---|---|
| [references/etapa4/revision_ejemplos_stefania.md](../../references/etapa4/revision_ejemplos_stefania.md) | Stefania: revisión de tres ejemplos; PR #55, revisado por Marco |
| [references/etapa4/revision_uso_diego_martinez.md](../../references/etapa4/revision_uso_diego_martinez.md) | Diego Martinez: endpoints, errores y uso; PR #58, revisado por Marco |
| [Revisión independiente del PR #49](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49#pullrequestreview-5779409126) | Diego Hurtado: 22 archivos, 76 pruebas, construcción Docker y 72 casos HTTP |
| [PR #50](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/50) | Marco: publicación de evidencias finales; aprobado por Diego Hurtado e integrado |

El historial muestra contribuciones de los cuatro integrantes, con alcances diferentes. La implementación asumida por Marco no se atribuye a sus compañeros. Esta evidencia de participación no garantiza una distribución equitativa del esfuerzo ni una calificación determinada.

## Qué se conserva fuera de Git y límites

El paquete de P1, su ZIP, CSV, bases de MLflow, entornos y credenciales permanecen fuera del repositorio. El manifiesto y las instrucciones permiten comprobar el modelo recibido por el canal del equipo o recuperado del Registry autorizado. No falta subir el ZIP a GitHub.

La entrega acredita inferencia local y los casos documentados. No acredita despliegue público autenticado, pruebas de carga, auditoría de la imagen base, ejecución con Podman ni exactitud predictiva sobre viajes nuevos. Se mantienen las advertencias de Starlette y de diferencias con las dependencias históricas del modelo. Los escaneos publicados conservan su fecha; esta revisión documental no es una auditoría nueva de vulnerabilidades.
