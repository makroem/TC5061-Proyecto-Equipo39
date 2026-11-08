# Distribución vigente y continuidad — Etapa 4

Actualización: 8 de noviembre de 2026. Estado contrastado con las integraciones y revisiones de GitHub.

| Persona | Trabajo principal | Respaldo / dependencia |
|---|---|---|
| Marco | Completado: recuperación y verificación del modelo; catálogo histórico; esquemas, adaptador, API, pruebas y Containerfile; reproducción desde un clon y entorno nuevos; documentación, capturas e integración de PR aprobados. | La revisión independiente del servicio y de su evidencia ya fue aprobada por Diego Hurtado en los PR #49 y #50. Cualquier nuevo cambio conserva la revisión por otra persona. |
| Diego Hurtado | Completado: comprobación independiente del paquete, contenedor y paridad; revisión del servicio y de las evidencias finales. | Aprobaciones de los PR #45, #46, #49 y #50. Su ejecución está documentada en la revisión del PR #49. |
| Stefania | Completado: revisión de tres ejemplos de entrada, documentada en el [PR #55](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/55), revisado por Marco e integrado. | [Tarea #47 cerrada](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/47). No hay dependencia pendiente para el servicio. |
| Diego Martinez | Completado: revisión de endpoints, respuestas y claridad de instrucciones, documentada en el [PR #58](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/58), revisado por Marco e integrado. | [Tarea #48 cerrada](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/48). No hay dependencia pendiente para el servicio. |

La implementación de `schemas.py`, `predictor.py` y `app.py` ya no depende de una aportación de Stefania o Diego Martinez. Sus revisiones ayudan a comprobar la claridad del servicio, pero no son requisitos para construir, probar o revisar los cambios críticos.

Toda integración conserva una revisión real por otra persona y las protecciones de `main`. Marco no aprueba sus propios PR. El trabajo técnico asumido por Marco o Diego Hurtado no se atribuye a otro integrante ni sustituye la evidencia individual que exige la actividad.

## Cierre

1. Completado: Diego Hurtado aprobó los PR [#45](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/45) y [#46](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/46); Marco los integró en `main` respetando las protecciones. La base resultante es `3c38b435269204729297342fc2f0013f6be455bb`.
2. Completado: Marco comprobó en una copia limpia de ese commit la descarga del catálogo, sin copia local, caché ni sesión de Google. Coincidieron las 484 filas, los 40,841 bytes y la huella del manifiesto; 51 pruebas de ingesta aprobadas. Se reutilizó el entorno de Python, por lo que esta comprobación no sustituye una instalación completa desde cero.
3. Completado: Marco incorporó `main` a la rama de la API, resolvió el conflicto de documentación conservando ambos procedimientos y ejecutó las 76 pruebas del servicio, todas aprobadas.
4. Completado: Diego Hurtado verificó el ZIP, los 22 archivos, 76 pruebas, la construcción de Docker, el estado saludable y 72 casos HTTP sin diferencias. Su [aprobación independiente](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49#pullrequestreview-5779409126) corresponde al último commit de la rama, `b350147`. Marco integró el [PR #49](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49) con esa aprobación vigente, sin omitir protecciones ni eliminar ramas.
5. Completado: Marco verificó `main` en `b1ddc47a0234def92b23c5ae7d6804f05e34697f` desde un clon nuevo y un entorno de Python nuevo. La instalación y `pip check` terminaron correctamente, 76 pruebas aprobaron y la nueva imagen Linux respondió 72 casos HTTP con diferencia máxima 0.0. El contenedor estaba saludable durante esa ejecución del 4 de noviembre; las capturas corresponden a esa imagen. El [cierre sobre main](../../reports/etapa4/cierre_api_marco_20261103.md#cierre-sobre-main) conserva resultados y límites. La validación del contenedor de Diego Hurtado ya no es una dependencia pendiente.
6. Completado: el 7 de noviembre Marco revisó e integró los PR #55 y #58. Sus documentos conservan la autoría y el alcance de las comprobaciones de Stefania y Diego Martinez; las tareas #47 y #48 quedaron cerradas.
7. Completado: el 8 de noviembre Diego Hurtado aprobó el [PR #50](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/50) y Marco lo integró mediante merge normal. Las evidencias finales del servicio ya están en `main`, en el commit `b6bd0afd13a775431152df0b3f16e324b83a14c7`.

## Participación individual

Las aportaciones de Stefania y Diego Martinez y sus revisiones por Marco ya están integradas. Diego Hurtado realizó la comprobación independiente del contenedor y revisó los cambios de Marco. No se requiere un PR adicional de Diego Hurtado para que Marco complete una revisión: Marco ya revisó los PR #55 y #58 de otros integrantes.

El historial acredita aportaciones de los cuatro integrantes, con alcances distintos. No acredita por sí solo una distribución equitativa del esfuerzo ni permite atribuir a otra persona el trabajo asumido por Marco. El [índice de entrega](../../reports/etapa4/indice_entrega_marco.md) reúne los archivos, resultados y revisiones. La actualización documental de este estado se integra mediante PR con revisión independiente; no vuelve a abrir las tareas técnicas cerradas.
