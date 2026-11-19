# Cierre de revisión de la Etapa 6

Corte: 19 de noviembre de 2026, America/Mexico_City. Registro documental de Marco.

## Integración y aprobación

- [PR #72](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/72): integrado en `main` el 19 de noviembre a las 09:18:19, mediante `7c49a8193746d3ac08e76619732a5905ca51d3f3`.
- [Revisión de Diego Hurtado](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/72#pullrequestreview-5969054034): APPROVED sobre `a9d8424ceb5090c7a4cc5b0aaeb9fc27e067db60`, enviada el 18 de noviembre a las 21:50:50, hora de Ciudad de México (19 de noviembre, 03:50:50 UTC).
- Los seis controles del PR estaban correctos antes de integrar. La [ejecución posterior sobre main](https://github.com/makroem/TC5061-Proyecto-Equipo39/actions/runs/44553281639) finalizó correctamente: pruebas de API y operación en Windows y Linux, construcción y despliegue temporal, comprobación HTTP y persistencia. El modelo de CI es sintético y está identificado; no sustituye P1 real.

## Alcance del contraste independiente

Diego Hurtado declaró que comprobó salud de API y tracking, identidad de P1, lotes de 1, 10 y 100, rechazo 422 del lote vacío y persistencia al recrear tracking. También declaró pruebas de carga con 1, 10 y 30 usuarios sin fallos y dentro de los objetivos de su ejecución; contrastó las 81 estimaciones FinOps y la integridad del informe. Su conclusión no contiene observaciones bloqueantes para integrar.

Las nueve mediciones originales de Marco mantienen los incumplimientos de latencia en 10 y 30 usuarios. La aprobación independiente no los convierte en resultados aprobados ni demuestra una mejora del código. Son ejecuciones distintas y deben conservarse por separado.

La revisión pública no adjunta los valores p95, duraciones, archivos de Locust, versiones del entorno o muestras de recursos de Diego Hurtado. Por ello, este cierre referencia su declaración y no inventa una tabla numérica de contraste. Si se incorporan esos archivos, deben conservar nombre de responsable, equipo, protocolo, fecha, commit y huellas. Aún se requieren ensayos comparables para atribuir diferencias al anfitrión o a una optimización.

## Informe y evidencia conservados

El [informe editable](../../references/etapa6/TC5061_Microservicios_FinOps_Equipo39.docx) conserva la huella SHA-256 `a536f74c53b256994e1580058f2ba3dcd2f242b4a5ea9c6be1196f44b6409394`, revisada por Diego Hurtado. Las frases de revisión pendiente del cuerpo describen su corte del 18 de noviembre; este registro documenta la aprobación posterior. No se modifican sus tablas, gráficas, métricas ni anexos.

El [registro de revisión](../../references/etapa6/checks/revision_independiente.json) identifica aprobación, cambio revisado y commit de integración. Las [mediciones de Marco](../../references/etapa6/mediciones_marco/) conservan el protocolo y los archivos originales. Los estados incluidos en esos archivos son históricos y no sustituyen este cierre. Las entregas de etapas anteriores permanecen en el mismo repositorio.

## Respaldo documental y continuidad

Marco preparó la [interpretación breve](interpretacion_carga.md) y las [seis verificaciones](verificacion_documental.md) previstas como respaldo de #75 y #76. Stefania y Diego Martínez pueden revisarlas y añadir sus observaciones desde ramas propias. Estos documentos no se atribuyen a ellos.

La integración de #72 está concluida. Las mejoras de rendimiento, la publicación de los archivos del contraste independiente y las aportaciones individuales complementarias se siguen por separado; no se presentan como resultados ya realizados. La actualización documental posterior a #72 requiere su propio registro de revisión y no hereda la aprobación del código anterior.
