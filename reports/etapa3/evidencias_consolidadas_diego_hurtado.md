# Consolidación de evidencias — Etapa 3



**Proyecto:** MiBici — Equipo 39

**Curso:** TC5061

**Responsable:** Diego Hurtado

**Actividad:** Consolidación del README y evidencias de calidad, pruebas y seguridad.



## 1. Objetivo



Consolidar y organizar las evidencias técnicas correspondientes a la Etapa 3 del proyecto MiBici Equipo 39, integrando los resultados documentados de los cuatro integrantes y diferenciando las verificaciones preliminares de la validación final.



Esta consolidación busca facilitar la revisión de resultados, conservar la trazabilidad de las ejecuciones y permitir la identificación de los hallazgos pendientes.



## 2. Estado de integración

Las contribuciones técnicas de P1, P2, P3, DeepChecks e infraestructura de calidad se encuentran integradas en `main`.

El PR #37 incorporó la primera consolidación documental de Diego Hurtado. El PR #38 de Marco incorporó el cierre integrado, las correcciones de dependencias y sus resultados de verificación.

**Commit de integración final:** `fd28d965465cadd5a736253cace0b3c23c92820b`.

La política `references/etapa3/quality_policy.json` permanece congelada con `frozen: true`, sin cambios en las reglas ni los umbrales.

La verificación inicial del código integrado corresponde al commit `03e1143`. Después de corregir las dependencias se ejecutó nuevamente la suite completa sobre `0dd8c6e`, con 238 pruebas aprobadas.

La validación final sobre datos reales se realizó una sola vez, con la política congelada. Sus resultados fueron 100 PASS, 3 WARN, 0 FAIL y 0 NOT_EVALUATED.

Los resultados técnicos están publicados y documentados. Las [nueve capturas originales del cierre](capturas_finales_20261101.md) fueron revisadas visualmente y verificadas contra su manifiesto durante la revisión del PR #40.


## 3. Inventario de capturas preliminares



Las imágenes originales fueron publicadas por Marco en `reports/figures/etapa3/`.



| ID | Evidencia | Contenido | Alcance |
|---|---|---|---|
| E01 | [Entornos](../figures/etapa3/E01_entornos.jpg) | Versiones del entorno de calidad y DeepChecks | Verificación de entorno |
| E02 | [Estructura](../figures/etapa3/E02_estructura.jpg) | Inventario de archivos versionados | Estado del commit comprobado |
| E03 | [Ingesta](../figures/etapa3/E03_ingesta.jpg) | 43 pruebas aprobadas y cobertura de ingesta | Ejecución parcial |
| E04 | [DeepChecks positivo](../figures/etapa3/E04_deepchecks_variable.jpg) | Aceptación de una columna variable | Datos sintéticos |
| E05 | [DeepChecks negativo](../figures/etapa3/E05_deepchecks_constante.jpg) | Detección de una columna constante | Datos sintéticos |
| E06 | [Suite sintética](../figures/etapa3/E06_suite_sintetica.jpg) | 155 pruebas aprobadas y cobertura global | Ejecución preliminar |
| E09 | [Seguridad](../figures/etapa3/E09_seguridad.jpg) | Bandit, dependencias e historial | Diagnóstico preliminar |
| E10 | [Exclusiones](../figures/etapa3/E10_exclusiones.jpg) | Comprobación de reglas de exclusión | Control de archivos |
| E12 | [Dependencias](../figures/etapa3/E12_actualizacion_dependencias.jpg) | Actualización parcial de dependencias | Verificación posterior |



Las capturas E04 y E05 muestran resultados originales de DeepChecks obtenidos con datos sintéticos. Las demás contienen registros exportados de ejecuciones o comprobaciones y no deben presentarse como capturas directas de consola.



La numeración se conserva conforme al inventario original. No se crean ni atribuyen imágenes para los identificadores ausentes.



## 4. Procedencia de las evidencias



La documentación original de Marco se encuentra en:



- [Inventario de capturas de Marco](evidencias_marco.md)

- [Manifiesto de evidencias](evidencias_manifest.json)

- [Resultados iniciales de Marco](avance_marco.md)

- [Actualización de dependencias](actualizacion_dependencias.json)



El manifiesto contiene hashes SHA256, fechas y descripciones de origen de las capturas preliminares.



La evidencia E12 corresponde a una actualización posterior y conserva información adicional en `actualizacion_dependencias.json`.



Los resultados originales deben permanecer disponibles sin modificaciones de sus imágenes, cifras o archivos de procedencia.



## 5. Evidencias técnicas de los integrantes



### 5.1 P1 — Stefania



[Revisión de calidad y seguridad de P1](revision_p1_stefania.md)



Incluye pruebas de calendario, variables cíclicas, partición cronológica, condiciones límite, entrenamiento con entradas inválidas y revisión del uso de `pickle`.



Las pruebas utilizan datos sintéticos y no sustituyen la validación de datos reales.



### 5.2 P2 y DeepChecks — Diego Martínez



[Motor y evaluación de calidad](calidad_datos_diego_martinez.md)



Se implementó el motor `mibici_equipo39/validation/data_checks.py` y la política configurable de calidad.



La ejecución documentada de desarrollo reportó:



| Estado | Resultado |
|---|---:|
| PASS | 64 |
| WARN | 2 |
| FAIL | 1 |
| NOT_EVALUATED | 0 |



El FAIL corresponde a una discrepancia de hash lógico de `stations.parquet` en macOS ARM, investigada junto con Marco y asociada a diferencias mínimas de representación numérica en coordenadas.



El resultado no debe ocultarse modificando arbitrariamente los manifiestos ni los criterios de calidad.



La suite combinada reportó 229 pruebas aprobadas antes del cierre final independiente.



### 5.3 P3 — Diego Hurtado



[Revisión de calidad y seguridad de P3](revision_p3_diego_hurtado.md)



Se incorporaron 12 pruebas adicionales orientadas a perfiles horarios, normalización, agrupamiento, condiciones límite y aislamiento entre periodos.



La verificación original documentó 52 pruebas conjuntas de P3 aprobadas y un hallazgo B403 de severidad baja asociado a la importación de `pickle`.



Los resultados corresponden a la ejecución identificada en dicho documento y no deben confundirse con los de la suite integrada posterior.



### 5.4 Infraestructura y seguridad — Marco



[Verificaciones iniciales](avance_marco.md) y [hallazgos de seguridad](hallazgos.md).



Comprenden pruebas de ingesta, verificación de manifiestos, compatibilidad de entornos, auditorías de dependencias y exclusiones de archivos sensibles.



Las observaciones abiertas requieren seguimiento y no deben interpretarse como una certificación de ausencia de vulnerabilidades.



## 6. Validación final integrada

**Estado: validación técnica final ejecutada y documentada.**

Marco realizó la verificación integrada sobre el código de `main` con Python 3.11.9, utilizando un clon nuevo y entornos independientes.

### 6.1 Pruebas automatizadas

| Indicador | Resultado |
|---|---|
| Pruebas aprobadas | 238 |
| Fallos | 0 |
| Errores | 0 |
| Pruebas omitidas | 0 |
| Advertencias de PyTest | 23 |
| Cobertura global | 82.14 % |
| Líneas cubiertas | 1,725 de 2,100 |

La suite se ejecutó inicialmente sobre `03e1143` y nuevamente con las dependencias corregidas sobre `0dd8c6e`. Ambas ejecuciones reportaron 238 pruebas aprobadas.

Fuentes:
- [Cierre integrado de Marco](cierre_integrado_marco_20261101.md)
- [Resultados estructurados del cierre](cierre_integrado_marco_20261101.json)
- [Revisión posterior a las correcciones](revision_pr38_20261101.json)

### 6.2 Validación final de datos

| Estado | Resultado |
|---|---:|
| PASS | 100 |
| WARN | 3 |
| FAIL | 0 |
| NOT_EVALUATED | 0 |

Las tres advertencias corresponden a variables constantes en perfiles horarios de P3 durante determinadas horas de madrugada.

Estas condiciones permanecen registradas como advertencias, sin modificar los modelos, la política de calidad ni los manifiestos oficiales.

Se verificaron 155 archivos procesados mediante SHA256 y 151 hashes lógicos del manifiesto oficial. La descarga anual no se repitió.

Fuente: [Validación final de datos](validacion_final_datos_20261101.json).

### 6.3 Seguridad y dependencias

La revisión de seguridad documentó ocho observaciones de severidad baja en Bandit, sin hallazgos de severidad media o alta.

Las versiones corregidas del entorno de calidad pasaron las verificaciones de compatibilidad y dependencias. La auditoría de los requisitos candidatos no encontró avisos conocidos en los paquetes revisados del entorno principal.

El entorno independiente de DeepChecks conserva dos avisos conocidos relacionados con `setuptools 81.0.0`. Estos hallazgos permanecen abiertos, con restricciones de uso y seguimiento asignado a Marco y Diego Martínez.

Fuente: [Reporte de seguridad del cierre](seguridad_cierre_20261101.json).

### 6.4 Evidencia visual del cierre

Las nueve capturas históricas identificadas en este documento corresponden a verificaciones preliminares y se conservan con su procedencia original.

Marco incorporó [nueve capturas originales del cierre](capturas_finales_20261101.md), con su [manifiesto de procedencia y hashes](capturas_finales_20261101.json). Incluyen el HTML original de DeepChecks y vistas de los registros de pruebas y seguridad. Los JSON siguen siendo registros documentales; las imágenes corresponden a su consulta posterior en navegador, no a una ejecución en vivo.

Diego Hurtado revisó las nueve capturas F01-F09, verificó sus hashes SHA256, tamaños, dimensiones y correspondencia con los reportes originales. El PR #40 fue aprobado e integrado en main.



## 7. Consideraciones de reproducibilidad



Los documentos de evidencia deben identificar la ejecución de origen, su alcance y sus limitaciones.



Las pruebas sintéticas acreditan comportamientos específicos del software, pero no garantizan por sí solas la calidad de los conjuntos reales.



Los datos originales de MiBici, los modelos, las bases de MLflow y los artefactos privados no deben incorporarse al repositorio público.



## 8. Estado de la consolidación

**Estado documental: actualizado con los resultados del cierre técnico integrado.**

La consolidación realizada por Diego Hurtado incluye:

- Documentación de las contribuciones de los cuatro integrantes.
- Inventario de nueve capturas preliminares con sus rutas y limitaciones.
- Referencias a los resultados originales de P1, P2, P3 y DeepChecks.
- Resultados finales de las 238 pruebas automatizadas y su cobertura.
- Validación final de datos con 100 PASS, 3 WARN, 0 FAIL y 0 NOT_EVALUATED.
- Resultados de las verificaciones de seguridad y dependencias.
- Trazabilidad mediante commits, reportes y documentos originales.

El README principal fue actualizado con los resultados integrados mediante el PR #38 y contiene el enlace a esta consolidación documental.

### Cierre de la consolidación visual

Las capturas y sus referencias ya están incorporadas en el inventario de Marco. La revisión visual fue completada por Diego Hurtado y las evidencias se integraron mediante el PR #40.

Los dos avisos conocidos del entorno DeepChecks permanecen bajo seguimiento técnico de Marco y Diego Martínez.

La validación técnica final y la consolidación visual están documentadas e integradas en main. Esta distinción evita presentar resultados históricos como si correspondieran a la ejecución definitiva.
