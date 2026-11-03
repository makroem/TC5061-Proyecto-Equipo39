# Arranque de Marco — Etapa 4

> Seguimiento histórico. Para las responsabilidades vigentes desde el 3 de noviembre, consultar [distribución actual](../../references/etapa4/distribucion_actual.md).

Fecha: 2 de noviembre de 2026. Repositorio: TC5061-Proyecto-Equipo39.
Base: `5344be3498bd3d46459c7e905e341fd6f5aec0c2` (main).

## Trabajo realizado

1. Se creó la rama `feat/marco-etapa4-modelo` desde la base integrada, separada de los PR #42 y #43 que seguían abiertos al iniciar.
2. Se comprobó el esquema existente y se reinició el servidor local oficial de MLflow en el puerto 5000. Se consultó el Registry sin crear versiones ni modificar aliases.
3. P1 `champion` resolvió a versión 1, run `66414a8b45164d3a8f5b9f42e7cb387b`, variante baseline. Se descargaron 22 archivos y se guardó el manifiesto en `references/etapa4/model_manifest.json`. El paquete del modelo no se sube a Git.
4. Se implementaron exportación, validación de inventario, carga local y comprobación de paridad independiente. Otra descarga mediante el manifiesto produjo el mismo hash del paquete: `dedce1eb08bda971a42fba311224c88e56f75cd2789dbb391e9445951931bd80`.
5. Se instaló un entorno aislado con los requisitos de servicio y desarrollo. `pip check` no encontró dependencias incompatibles. Todos sus paquetes quedaron fijados; no se cambió el entorno completo de entrenamiento ni el del servidor oficial.
6. Se publican contrato inicial, instrucciones de reproducción, pruebas, manifiesto y reportes verificables. La revisión del PR corresponde a Diego Hurtado.

## Pruebas ejecutadas

| Comprobación | Resultado | Alcance |
|---|---|---|
| Suite previa en main | 238 pasaron, 0 fallos, 0 errores; 306.89 s | Entorno completo de la etapa anterior. |
| Suite nueva | 31 pasaron, 0 fallos, 0 errores; 1.14 s | Entorno aislado de servicio; pruebas unitarias sin Registry real. |
| Comparación real de P1 | 72 entradas, diferencia máxima 0.0 | Paquete local contra versión numérica del Registry en proceso independiente. |
| Repetición de predicciones | Idénticas | Mismo modelo y entradas, sin reentrenar. |
| Inferencia local sin solicitudes HTTP | Correcta | Se bloqueó requests durante carga y predicción locales. No equivale a probar aislamiento de red de un contenedor. |
| Integridad después de cargar | Sin cambios | Las 22 huellas siguen coincidiendo. |
| Reproducción desde manifiesto | Correcta | Otro destino local; no resuelve nuevamente el alias. |
| Dependencias | 67 paquetes auditados, 0 vulnerabilidades conocidas | Requisitos de servicio; no cubre todavía una imagen Linux. |
| Bandit | 1 aviso LOW, 0 MEDIUM, 0 HIGH | Importación de subprocess en la comprobación independiente; ver revisión de seguridad. |

La primera ejecución de la suite anterior encontró 92 errores de preparación por permisos del directorio temporal de Windows. Se repitió usando una carpeta temporal nueva dentro del proyecto; el resultado válido es 238 pruebas aprobadas. No se cambió código ni se omitieron pruebas para resolver esa incidencia.

El paquete registrado conserva las dependencias históricas de entrenamiento. MLflow advierte diferencias al cargarlo en el entorno reducido actual. La paridad comprobada cubre estas 72 entradas y Windows; no constituye una demostración universal de equivalencia para cualquier entrada ni una validación Linux.

## Archivos que permiten continuar

- [Contrato para esquemas, API y contenedor](../../references/etapa4/contrato_api.md).
- [Manifiesto del modelo](../../references/etapa4/model_manifest.json).
- [Resultado de paridad](paridad_modelo_marco.json).
- [Resumen verificable de pruebas](verificacion_marco.json).
- [Revisión de seguridad](seguridad_api.md).
- [Captura original del Registry de P1 y procedencia](captura_registry_p1.md).

## Evidencia del Registry completada

El 2 de noviembre de 2026 se incorporó la captura E02 proporcionada por Marco. Muestra el servidor local oficial en el puerto 5000, el modelo `mibici-equipo39-p1-demanda`, su versión 1 y el alias `champion`. La corrida de origen, el commit y la versión de datos visibles coinciden con el manifiesto del modelo. Se conserva el PNG original sin recortes ni modificaciones; la huella y el alcance están en el [registro de la captura](captura_registry_p1.md).

## Pendientes y responsables

| Pendiente | Responsable | Insumo disponible / dependencia |
|---|---|---|
| Revisar este PR | Diego Hurtado | Exportador, cargador, manifiesto, pruebas y contrato. |
| Implementar contrato Pydantic y adaptador tabular | Stefania | Firma y tipos del manifiesto; cargador listo. |
| Implementar FastAPI y pruebas HTTP | Diego Martinez | Puede avanzar con fixtures; integra esquemas de Stefania y cargador de Marco. |
| Containerfile, exclusiones y prueba Linux | Diego Hurtado, con Marco para dependencias | Requisitos preparados; construcción completa necesita API y esquemas. |
| Reproducción desde clon limpio y captura del contenedor | Marco y Diego Hurtado | Requiere módulos integrados y revisados. |

No se declara terminada la etapa 4: este PR entrega el arranque técnico y los insumos de Marco. La evidencia de una API respondiendo desde un contenedor se obtendrá después de integrar los módulos restantes.
