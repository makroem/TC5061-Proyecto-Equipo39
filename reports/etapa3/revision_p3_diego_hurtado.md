# Revisión de calidad y seguridad de P3 — Etapa 3



**Proyecto:** MiBici — Equipo 39

**Curso:** TC5061

**Responsable:** Diego Hurtado (Persona 4)

**Componente:** P3 — Agrupamiento de estaciones



## 1. Objetivo



Ampliar las pruebas automatizadas de P3 y evaluar los hallazgos de seguridad de su implementación, como parte de las actividades de calidad de la Etapa 3.



La revisión se realizó en una rama independiente, sin modificar los modelos oficiales, los datos ni los resultados experimentales de la Etapa 2.



## 2. Ampliación de pruebas automatizadas



Se incorporó `tests/test\_stage3\_p3.py`, con 12 pruebas adicionales desarrolladas utilizando datos sintéticos.



Los casos amplían la cobertura de condiciones límite relacionadas con perfiles horarios, normalización, ponderaciones, estaciones sin registros, entradas inválidas, métricas de agrupamiento y aislamiento entre periodos de entrenamiento y evaluación.



### 2.1 Resultados obtenidos



| Ejecución | Resultado |

|---|---|

| Nuevas pruebas de Etapa 3 | 12 aprobadas |

| Pruebas conjuntas de P3 | 52 aprobadas |

| Suite completa del repositorio | 167 aprobadas |

| Fallos de la suite completa | 0 |

| Advertencias de PyTest | 32 |

| Duración de la suite completa | 67.16 segundos |



Los resultados muestran que los nuevos casos son compatibles con las pruebas existentes. No se detectaron regresiones mediante la suite ejecutada.



Sin embargo, estas pruebas no sustituyen la validación de calidad sobre los datos reales ni garantizan la ausencia de defectos fuera de los casos cubiertos.



## 3. Análisis estático de seguridad



Se utilizó Bandit 1.9.4, instalado en un entorno virtual independiente para evitar modificaciones en las dependencias del proyecto.



**Archivo analizado:** `mibici\_equipo39/modeling/p3.py`



**Comando ejecutado:**



```powershell

\& "$env:TEMP\\tc5061-bandit\\Scripts\\python.exe" -m bandit .\\mibici\_equipo39\\modeling\\p3.py -f txt

```



### 3.1 Resultados



| Indicador | Resultado |

|---|---|

| Líneas de código analizadas | 794 |

| Hallazgos de severidad alta | 0 |

| Hallazgos de severidad media | 0 |

| Hallazgos de severidad baja | 1 |

| Regla identificada | B403 |

| Confianza del hallazgo | Alta |

| Ubicación | Línea 11 |



### 3.2 Análisis del hallazgo B403



Bandit identificó la importación del módulo `pickle`, cuya utilización puede representar riesgos de seguridad cuando se deserializan objetos provenientes de fuentes no confiables.



En la implementación revisada, `pickle.dumps()` se utiliza para medir el tamaño serializado de los modelos de clustering. Esta información forma parte de las métricas de costo empleadas para comparar alternativas y resolver empates.



No se identificaron llamadas a `pickle.load()` ni a `pickle.loads()` dentro del archivo analizado.



Los objetos serializados corresponden a modelos generados durante el proceso local de experimentación. Por ello, el hallazgo se considera de riesgo bajo en el contexto evaluado, siempre que los modelos utilizados provengan de fuentes confiables.



### 3.3 Decisión técnica



Se decidió conservar el mecanismo actual de medición del tamaño serializado para no alterar los criterios experimentales establecidos previamente.



El hallazgo queda documentado con su justificación técnica. No se añadieron exclusiones de Bandit ni comentarios `nosec` para ocultar la advertencia.



Como medida preventiva, se recomienda evitar la deserialización de archivos de origen desconocido y verificar la procedencia de los artefactos antes de cargarlos.



## 4. Limitaciones y actividades complementarias



El análisis de Bandit es estático y no garantiza la ausencia total de vulnerabilidades.



La revisión se limita al componente P3 y no sustituye la auditoría de dependencias del sistema completo.



Asimismo, las pruebas adicionales utilizan datos sintéticos. La verificación de calidad sobre datos reales, incluyendo el uso de DeepChecks y los manifiestos oficiales, corresponde al proceso de integración y validación del equipo.



Las 32 advertencias de PyTest deberán analizarse por separado, pues no equivalen a los hallazgos de seguridad de Bandit.



## 5. Conclusión



La ampliación de pruebas de P3 terminó satisfactoriamente: las 12 pruebas nuevas, las 52 pruebas conjuntas de P3 y las 167 pruebas de la suite completa fueron aprobadas.



El análisis de seguridad identificó un único hallazgo de severidad baja relacionado con la importación de `pickle`. Se revisó su utilización, se documentó el riesgo y se justificó conservar el comportamiento actual.



Estos resultados aportan evidencia de calidad y seguridad de P3 para la Etapa 3, sin modificar los modelos ni las selecciones oficiales.
