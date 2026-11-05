# Distribución vigente y continuidad — Etapa 4

Actualización: 4 de noviembre de 2026. Reasignación solicitada por Marco.

| Persona | Trabajo principal | Respaldo / dependencia |
|---|---|---|
| Marco | Recuperar el catálogo original con validación de huella; implementar esquemas, adaptador, API, pruebas y Containerfile; integrar los PR aprobados. | Revisión independiente de Diego Hurtado. El respaldo compartido del CSV ya está publicado y su descarga sin credenciales fue verificada en el PR #46. |
| Diego Hurtado | Revisar los PR de Marco, comprobar el contenedor y la paridad del modelo; revisar la evidencia final. | Marco deja código, comandos y resultados. Puede realizar la comprobación en su máquina sin esperar a Stefania o Diego Martinez. |
| Stefania | Revisar tres ejemplos de entrada y documentar valores válidos e inválidos en un PR pequeño. [Tarea #47](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/47). | Sin cambios en el servicio ni en los modelos. Marco o Diego Hurtado pueden cubrir la revisión técnica si se necesita. |
| Diego Martinez | Revisar la tabla de endpoints y la claridad de instrucciones, con un PR pequeño de documentación. [Tarea #48](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/48). | No requiere datos, entrenamiento ni acceso al Registry. Marco o Diego Hurtado pueden cubrir las correcciones. |

La implementación de `schemas.py`, `predictor.py` y `app.py` ya no depende de una aportación de Stefania o Diego Martinez. Sus revisiones ayudan a comprobar la claridad del servicio, pero no son requisitos para construir, probar o revisar los cambios críticos.

Toda integración conserva una revisión real por otra persona y las protecciones de `main`. Marco no aprueba sus propios PR. El trabajo técnico asumido por Marco o Diego Hurtado no se atribuye a otro integrante ni sustituye la evidencia individual que exige la actividad.

## Cierre

1. Completado: Diego Hurtado aprobó los PR [#45](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/45) y [#46](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/46); Marco los integró en `main` respetando las protecciones. La base resultante es `3c38b435269204729297342fc2f0013f6be455bb`.
2. Completado: Marco comprobó en una copia limpia de ese commit la descarga del catálogo, sin copia local, caché ni sesión de Google. Coincidieron las 484 filas, los 40,841 bytes y la huella del manifiesto; 51 pruebas de ingesta aprobadas. Se reutilizó el entorno de Python, por lo que esta comprobación no sustituye una instalación completa desde cero.
3. Completado: Marco incorporó `main` a la rama de la API, resolvió el conflicto de documentación conservando ambos procedimientos y ejecutó las 76 pruebas del servicio, todas aprobadas.
4. Completado: Diego Hurtado verificó el ZIP, los 22 archivos, 76 pruebas, la construcción de Docker, el estado saludable y 72 casos HTTP sin diferencias. Su [aprobación independiente](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49#pullrequestreview-5779409126) corresponde al último commit de la rama, `b350147`. Marco integró el [PR #49](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/49) con esa aprobación vigente, sin omitir protecciones ni eliminar ramas.
5. Completado: Marco verificó `main` en `b1ddc47a0234def92b23c5ae7d6804f05e34697f` desde un clon nuevo y un entorno de Python nuevo. La instalación y `pip check` terminaron correctamente, 76 pruebas aprobaron y la nueva imagen Linux respondió 72 casos HTTP con diferencia máxima 0.0. El contenedor está saludable y las capturas nuevas corresponden a esa imagen. El [cierre sobre main](../../reports/etapa4/cierre_api_marco_20261103.md#cierre-sobre-main) conserva resultados y límites. La validación del contenedor de Diego Hurtado ya no es una dependencia pendiente.

## Participación individual

Las tareas #47 (Stefania) y #48 (Diego Martinez) continúan abiertas y sin nuevas aportaciones en esta revisión. Sus cambios son acotados y no detienen el cierre técnico de la API. Cada integrante conserva la responsabilidad de aportar y revisar con su propia cuenta; cubrir una tarea técnica no acredita participación de otra persona.

Diego Hurtado puede aportar su comprobación independiente del contenedor mediante un PR de evidencia. Marco podrá revisar ese PR para completar su revisión a otro integrante en esta etapa. Se trata del siguiente trabajo propuesto, no de una contribución ya realizada.
