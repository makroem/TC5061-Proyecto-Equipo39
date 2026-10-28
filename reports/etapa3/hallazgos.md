# Hallazgos preliminares de seguridad y ejecución

Revisión de Marco, 28 de octubre de 2026. Alcance: código del módulo, versiones
fijadas del proyecto, archivos versionados y referencias Git disponibles en el clon.
Esta revisión no sustituye la validación final después de integrar los PR de la Etapa 3.

Actualización posterior: la rama `fix/marco-a7-dependencias` propone versiones
corregidas de certifi, requests, pytest y python-dotenv. El auditor deja de reportar
avisos en esos cuatro paquetes, pero MLflow y PyArrow continúan abiertos.
Consultar los [resultados de la actualización](actualizacion_dependencias.json)
y su [procedimiento](../../references/etapa3/actualizacion_dependencias.md).
Los conteos y versiones que siguen se conservan como diagnóstico previo al cambio.

## Corregido: validaciones que desaparecían con optimización

Bandit identificó tres usos de `assert` en `dataset.py`: conservación de conteos y
dos comprobaciones de carpetas antes del borrado. Python omite esas expresiones con `-O`.
Ahora la conservación usa una excepción explícita y `remove_data_directory` comprueba
que el destino sea una subcarpeta de `data`, rechazando la propia raíz y rutas externas.
La misma función protege la limpieza final del directorio de construcción.

Las pruebas comprueban la eliminación de una carpeta temporal permitida y la
conservación de las carpetas rechazadas tanto en Python normal como con `-O`.
La ingesta anual sintética sigue reproduciendo su manifiesto. No se cambiaron reglas
de limpieza, fechas, particiones ni modelos.

## Bandit: cinco observaciones de severidad baja

| Código | Ubicación | Interpretación y seguimiento |
|---|---|---|
| B403 (2) | `modeling/p1.py`, `modeling/p3.py` | Se importa pickle para medir el tamaño serializado mediante `dumps`. Esto no ejecuta una carga de contenido externo. Mantener la restricción de cargar únicamente modelos de origen confiable; responsables de revisión: Stefania y Diego Hurtado. |
| B404, B603 | `modeling/tracking.py` | Se invoca Git con una lista de argumentos y sin shell. No se observó concatenación de entrada del usuario a una orden de shell. Diego Martinez debe revisar este contrato junto con las pruebas de trazabilidad. |
| B607 | `modeling/tracking.py` | El ejecutable se busca por PATH. Usar una instalación de Git conocida; evaluar una ruta resuelta explícitamente en la revisión del controlador. |

No se añadieron reglas de exclusión ni comentarios `nosec` para ocultar estos avisos.
El código de salida de Bandit sigue siendo 1 porque permanecen observaciones.

## Dependencias: avisos que requieren una actualización coordinada

La consulta de `pip-audit` sobre 119 paquetes fijados reportó 68 entradas en seis
paquetes. Hay identificadores repetidos: son 36 pares distintos de paquete e
identificador, no 68 vulnerabilidades independientes. El resultado completo se
conserva localmente; el resumen publicado mantiene los identificadores únicos.

| Paquete fijado | Siguiente paso | Responsables y dependencia |
|---|---|---|
| `mlflow==2.22.0` | Revisar los avisos aplicables y probar una migración compatible con Projects, artefactos, registro y carga por alias. No actualizar la base oficial directamente. | Marco y Diego Martinez; regresión de P1/P3 con Stefania y Diego Hurtado. |
| `pyarrow==19.0.1` | Probar la versión corregida con lectura/escritura Parquet y hashes lógicos antes de cambiar el entorno. | Marco; revisión del PR de dependencias. |
| `requests==2.32.3`, `certifi==2026.7.22` | Probar versiones corregidas con los contratos de descarga y el acceso HTTPS al proveedor. | Marco; revisión del PR de dependencias. |
| `pytest==8.3.5` | Probar la versión corregida con la colección y suite completa, manteniendo los mismos casos. | Marco y revisión del equipo. |
| `python-dotenv==1.0.1` | Comprobar carga de configuración sin exponer valores del entorno. | Marco y Diego Martinez. |

Los rangos corregidos publicados por el auditor se incluyen en `seguridad_resumen.json`;
son candidatos a evaluar, no versiones instaladas ni una recomendación de migrar sin pruebas.
No se ejecutó una actualización automática que alterara el entorno de entrenamiento
ya usado para las corridas oficiales. Estos avisos permanecen abiertos.

Los 19 requisitos adicionales de calidad no presentaron avisos conocidos en la consulta.
Ese resultado no cancela los hallazgos del entorno del proyecto.

## Secretos, archivos y alcance

El historial y el snapshot del commit se analizan por separado con Gitleaks 8.30.1
y redacción completa de valores. Las librerías instaladas y salidas privadas no se
mezclan con el snapshot versionado. El resultado y el número de commits revisados
se registran en el resumen de seguridad. La ausencia de hallazgos se limita a las
reglas de la herramienta y al alcance indicado; no es una garantía absoluta.

## Incidentes del entorno de prueba

- El primer intento encontró permisos incompatibles en el temporal compartido de
  Windows. Otro intento completo encontró el límite de longitud de rutas al copiar
  artefactos de MLflow. Se resolvieron ambos problemas con un directorio temporal
  nuevo y corto. La guía de ejecución documenta el procedimiento; la repetición
  completa terminó con 155 pruebas aprobadas. No se cambiaron permisos globales.
- DeepChecks 0.19.1 se instala bajo las restricciones del proyecto, pero falla al
  importar sus comprobaciones con NumPy 2.1.3 porque utiliza `np.Inf`. La prueba
  demuestra por qué `pip check` no basta para confirmar compatibilidad de ejecución.
  El entorno independiente ya ejecutó los controles positivo y negativo y exportó
  sus HTML correctamente. Se comprobó además la lectura de un Parquet sintético
  conservando columnas, conteos y hash lógico. No sustituye la validación real.
- En el entorno independiente se actualizó PyArrow de 19.0.1 a 23.0.1. La auditoría
  posterior de sus 112 paquetes no encontró avisos conocidos. Este cambio pertenece
  exclusivamente al entorno de DeepChecks; los avisos del entorno histórico siguen abiertos.

El cierre de seguridad requiere revisar los avisos de dependencias, las aportaciones
restantes y repetir los análisis sobre el código integrado. Una captura aprobada de
PyTest no debe presentarse como aprobación completa de seguridad.
