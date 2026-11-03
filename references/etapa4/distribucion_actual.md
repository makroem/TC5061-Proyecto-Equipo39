# Distribución vigente y continuidad — Etapa 4

Fecha: 3 de noviembre de 2026. Reasignación solicitada por Marco.

| Persona | Trabajo principal | Respaldo / dependencia |
|---|---|---|
| Marco | Recuperar el catálogo original con validación de huella; implementar esquemas, adaptador, API, pruebas y Containerfile; integrar los PR aprobados. | Revisión independiente de Diego Hurtado. El respaldo compartido del CSV ya está publicado y su descarga sin credenciales fue verificada en el PR #46. |
| Diego Hurtado | Revisar los PR de Marco, comprobar el contenedor y la paridad del modelo; revisar la evidencia final. | Marco deja código, comandos y resultados. Puede realizar la comprobación en su máquina sin esperar a Stefania o Diego Martinez. |
| Stefania | Revisar tres ejemplos de entrada y documentar valores válidos e inválidos en un PR pequeño. [Tarea #47](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/47). | Sin cambios en el servicio ni en los modelos. Marco o Diego Hurtado pueden cubrir la revisión técnica si se necesita. |
| Diego Martinez | Revisar la tabla de endpoints y la claridad de instrucciones, con un PR pequeño de documentación. [Tarea #48](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/48). | No requiere datos, entrenamiento ni acceso al Registry. Marco o Diego Hurtado pueden cubrir las correcciones. |

La implementación de `schemas.py`, `predictor.py` y `app.py` ya no depende de una aportación de Stefania o Diego Martinez. Sus revisiones ayudan a comprobar la claridad del servicio, pero no son requisitos para construir, probar o revisar los cambios críticos.

Toda integración conserva una revisión real por otra persona y las protecciones de `main`. Marco no aprueba sus propios PR. El trabajo técnico asumido por Marco o Diego Hurtado no se atribuye a otro integrante ni sustituye la evidencia individual que exige la actividad.

## Cierre

1. Diego Hurtado revisa los PR de catálogo, API y paridad ampliada.
2. Marco integra los cambios aprobados y resuelve conflictos si aparecen.
3. Marco y Diego Hurtado comprueban los comandos desde el contenido integrado y conservan capturas auténticas del contenedor.
4. El PR #46 incorpora la descarga remota verificada del catálogo histórico desde Google Drive. Después de integrarlo, comprobar su recuperación desde main. Esto no bloquea el servicio: la imagen incluye el modelo verificado y no consume CSV para predecir.
