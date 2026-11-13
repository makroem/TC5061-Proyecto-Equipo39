# Etapa 5: distribución de actividades

Actualización: 11 de noviembre de 2026. Esta distribución sustituye la asignación operativa del manual inicial; los criterios de evaluación se conservan.

| Orden | Actividad y resultado esperado | Responsable | Dependencia | Respaldo |
|---|---|---|---|---|
| 1 | Protocolo, recuperación de A, fuentes, huellas y preparación de referencia/actual | Marco | Modelo P1 y datos históricos de la etapa anterior | Diego Hurtado |
| 2 | Reporte Evidently, entrenamiento de B, comparación pareada, costos, estabilidad y recomendación | Marco | Datos y protocolo verificados | Diego Hurtado |
| 3 | Reproducir los controles, revisar fechas, pares, métricas y el PR técnico | Diego Hurtado | Código y resultados publicados en el PR | Otro revisor distinto del autor, si Diego Hurtado no está disponible |
| 4 | Revisión breve de interpretación: identificar tres variables relevantes y explicar por qué drift no equivale a pérdida de precisión; aportar 150–250 palabras con referencias al reporte | Stefania | `drift_variables.csv`, `drift.html` e interpretación preliminar | Marco redacta o corrige; Diego Hurtado valida. No bloquea el trabajo técnico |
| 5 | Comprobar ficha de A/B: nombre, versión, run, periodos y huella de datos. Aportar una tabla de seis verificaciones y cualquier discrepancia | Diego Martinez | `models.json`, `data_manifest.json` y resultados de comparación | Marco completa la ficha; Diego Hurtado la valida. No bloquea el trabajo técnico |
| 6 | Integrar el reporte de 3–5 páginas, capturas auténticas y referencias; confirmar que corresponde a los resultados revisados | Marco; revisión de Diego Hurtado | Resultados y revisión técnica | Marco puede integrar los aportes documentales faltantes |
| 7 | Resolver observaciones y fusionar el PR revisado; cualquier promoción es una decisión posterior y explícita | Marco | Revisión independiente de Diego Hurtado | No se sustituye la revisión independiente por la aprobación del autor |

Las tareas de Stefania y Diego Martinez son acotadas y pueden realizarse en paralelo una vez publicados sus insumos. No autorizan cambios de protocolo, reentrenamiento ni promoción. Si no están disponibles, Marco y Diego Hurtado cubren el contenido, conservando la autoría real de cada aporte. Esto permite avanzar técnicamente, pero no acredita la participación individual de una persona que no haya contribuido.

No se solicita reescribir el historial ni distribuir commits artificialmente. Cada aportación debe quedar en su rama y PR, con revisión y resultado verificables.

Asignaciones publicadas: [revisión de Stefania, #62](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/62) y [ficha de Diego Martinez, #63](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/63).
