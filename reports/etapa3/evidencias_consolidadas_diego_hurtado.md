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



El commit integrado utilizado como referencia inicial es `e9ac7fdf9f04428b0d56d3af1eb5fece543c6033`.



La política `references/etapa3/quality_policy.json` se encuentra congelada con `frozen: true`.



La integración de código no sustituye la ejecución final de calidad desde un clon limpio. Los resultados de dicha ejecución deberán incorporarse por separado.



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



**Estado: pendiente de incorporar evidencia de ejecución final.**



Con los PR técnicos integrados y la política congelada, Marco deberá documentar la reproducción independiente de las comprobaciones de calidad sobre el código integrado.



La consolidación final deberá registrar:



- Commit exacto, entorno y versiones de dependencias.

- Resultados de la suite completa de PyTest.

- Comprobación de datos, particiones y manifiestos.

- Resultados de DeepChecks en `--stage final`.

- Hallazgos de seguridad y seguimiento de vulnerabilidades.

- Evidencias visuales reales, fechas, procedencia y limitaciones.



No se asignan cifras finales ni identificadores de capturas que todavía no hayan sido publicados.



## 7. Consideraciones de reproducibilidad



Los documentos de evidencia deben identificar la ejecución de origen, su alcance y sus limitaciones.



Las pruebas sintéticas acreditan comportamientos específicos del software, pero no garantizan por sí solas la calidad de los conjuntos reales.



Los datos originales de MiBici, los modelos, las bases de MLflow y los artefactos privados no deben incorporarse al repositorio público.



## 8. Estado de la consolidación



La documentación técnica integrada y las nueve capturas preliminares están identificadas.



El README se encuentra en proceso de actualización por Diego Hurtado, mientras que la ejecución final integrada y sus capturas dependen de la verificación correspondiente de Marco.



La actividad documental podrá cerrarse cuando la evidencia final esté disponible, sus resultados sean consistentes con el código comprobado y los enlaces del README hayan sido revisados.
