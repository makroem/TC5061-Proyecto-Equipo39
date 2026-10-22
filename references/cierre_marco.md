# Registro de validación e integración de Marco

Actualización: 21 de octubre de 2026, America/Mexico_City.

## Trabajo realizado

Marco preparó estructura e ingesta, su versionado y auditoría; publicó y revisó correcciones; completó la implementación y evaluación de cierre; resolvió conflictos y coordinó la integración. Los PR #1, #2 y #4 conservan la evidencia de estructura e ingesta. Los PR #6 y #7 conservan las correcciones y los PR #8 y #3 la incorporación del cierre y su integración en main.

- [PR #8](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/8): aprobado por Stefania y Diego Hurtado e incorporado a la rama de integración.
- [PR #3](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/3): actualizado con main, revalidado e incorporado en `de5d622707254e275369d3e7c60d340523ce33ce` sin omitir las protecciones.
- [PR #5](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/5): cerrado sin merge para evitar volver a incorporar una versión anterior. El historial permanece disponible.

Marco realizó revisiones formales de los PR #3 y #5. Esto acredita esas revisiones concretas; no se inventa una revisión de un PR propio de Diego Hurtado, que no aparece en el historial consultado.

## Alcance de las comprobaciones

Las 39 pruebas se ejecutaron sobre `63c2abdaab6f98e5726c6b8b3c299d391dc93b6f`. Se comprobó que el árbol de archivos integrado en main es idéntico al probado. El problema inicial de permisos del temporal se resolvió usando una carpeta nueva del workspace, sin modificar el código. La ejecución anual anterior y sus seis runs de MLflow se conservan en `reports/cierre_experimentos.json`, vinculados a su commit original; no se afirma una nueva ejecución de MLflow sobre el commit de merge.

`reports/reproduccion_previa_cierre.json` es un registro histórico de una etapa anterior a los experimentos; no debe interpretarse como el estado actual del proyecto. `reports/Estado_Integracion_Marco.json` documenta la integración actual y distingue los alcances.

La actualización presente solo corrige documentación. El PDF y Word publicados mantienen la validación visual original de 18 páginas; no se editaron ni se presentan como nuevamente renderizados.

## Dependencias que no puede cerrar Marco por otro integrante

- Diego Hurtado debe acreditar su contribución y PR propio. Ya realizó la revisión del PR #8.
- El equipo debe contrastar las cuatro lecturas completas y confirmar las condiciones de uso de los CSV.
- El responsable del envío debe confirmar la entrega en Canvas y conservar el comprobante. No se puede determinar ese estado desde GitHub.

La rama `feat/persona1-ingesta` se conserva. Los cambios documentales posteriores se incorporan mediante PR revisado, manteniendo la protección de main.
