# Avance de Marco — Etapa 3

Fecha de comprobación: 28 de octubre de 2026. Rama: `chore/marco-a7-calidad`.
Repositorio: [TC5061-Proyecto-Equipo39](https://github.com/makroem/TC5061-Proyecto-Equipo39).
Código probado: `b00703251085ada10693d5b31fc69b99ab6640ae`.

Se preparó un clon independiente, se fijó el entorno de calidad y se ampliaron los
contratos de ingesta. La revisión encontró tres comprobaciones de seguridad que
desaparecían al ejecutar Python con optimización. Se sustituyeron por validaciones
explícitas y se comprobó que una limpieza no pueda borrar la raíz de datos ni una
carpeta externa. Los datos, las particiones y los modelos oficiales se conservaron.

## Resultados ejecutados

| Verificación | Resultado | Alcance |
|---|---|---|
| Colección de PyTest | 155 casos | Suite disponible en esta rama |
| Suite rápida | 123 aprobados; 32 deseleccionados | Sin integración ni validación real |
| Ingesta y regresiones asociadas | 43 aprobados; 25 avisos | Casos normales, límites, errores y seguridad de carpetas |
| Cobertura de `dataset.py` | 221 de 232 líneas; 95.26 % | Cobertura de líneas, no garantía de ausencia de defectos |
| Suite completa sintética | 155 aprobados; 32 avisos | Incluye los contratos existentes de MLflow, Git y HTTP local |
| Cobertura global | 1483 de 1845 líneas; 80.38 % | Sin excluir líneas del informe |
| DeepChecks separado | Control positivo aprobado y negativo rechazado | Compatibilidad con datos sintéticos; HTML consultados |
| Intercambio Parquet | Columnas, conteos y hash coincidentes | Archivo sintético entre los dos entornos |
| Bandit | Tres observaciones corregidas; cinco bajas abiertas | Módulo del proyecto |
| Dependencias del proyecto | 36 pares únicos paquete/aviso en seis paquetes | 68 entradas reportadas; seguimiento abierto |
| Dependencias adicionales de calidad | Sin avisos conocidos en 19 paquetes | Complementan, no sustituyen, el análisis del proyecto |
| Entorno independiente de DeepChecks | Sin avisos conocidos en 112 paquetes | Incluye PyArrow 23.0.1 |
| Secretos | Sin hallazgos en historial y snapshot analizados | 87 commits disponibles hasta el código probado |

Los avisos de PyTest se conservan en los registros completos. Los primeros intentos
fallidos por permisos y longitud de rutas también se conservaron de forma privada.
La ejecución completa aprobada utiliza una carpeta temporal nueva y corta.

Los resultados legibles por máquina están en [resultados_marco.json](resultados_marco.json),
[seguridad_resumen.json](seguridad_resumen.json) y
[deepchecks_compatibilidad.json](deepchecks_compatibilidad.json). Las capturas y sus
límites están en [evidencias_marco.md](evidencias_marco.md). Los hashes permiten
identificar el entorno, el script y los registros usados en esta comprobación.

## Estado frente al manual

| Actividad | Estado de Marco | Dependencia para continuar |
|---|---|---|
| M01. Contrato, rama e inventario | Preparados en esta rama | Revisión del contrato por el equipo |
| M02. Entorno y configuración de pruebas | Implementados y ejecutados | Revisión del PR por Stefania |
| M03. Compatibilidad de DeepChecks | Entorno independiente comprobado | Diego Martinez implementa el motor y la política; cada responsable revisa sus criterios |
| M04. Casos de ingesta | Implementados y aprobados | Revisión del PR por Stefania |
| M05. Seguridad y exclusiones | Diagnóstico y correcciones de ingesta realizados | Resolver los avisos de dependencias con una migración probada y revisada |
| M06. Colaboración | Aporte preparado para revisión independiente | Stefania revisa este PR; Marco revisará el aporte de Diego Hurtado cuando esté disponible |
| M07. Cierre integrado | Pendiente | PR técnicos de los cuatro integrantes revisados e integrados; política de calidad congelada |
| M08. Evidencia final y entrega | Evidencia preliminar disponible | Diego Hurtado consolida README/evidencias y el equipo acuerda el envío en Canvas |

## Siguiente trabajo y responsables

- Stefania: revisar esta aportación y completar los casos de P1, calendario y partición.
- Diego Martinez: implementar el motor y los umbrales de DeepChecks; completar P2 y
  los contratos de registro/controlador. El entorno ya está disponible para sus pruebas.
- Diego Hurtado: ampliar P3 y organizar las evidencias finales cuando estén integradas
  las comprobaciones del equipo.
- Marco: atender la revisión, preparar con el equipo la migración de dependencias,
  revisar el PR de Diego Hurtado y repetir el cierre sobre el código integrado.

La compatibilidad básica de DeepChecks no reemplaza el análisis de nulos, duplicados,
integridad y drift de los datos reales. La suite aprobada tampoco cierra los hallazgos
de seguridad. No se declara terminada la Actividad 7 ni verificado el envío en Canvas.
