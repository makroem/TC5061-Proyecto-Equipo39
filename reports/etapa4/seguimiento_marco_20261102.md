# Integración y ampliación de la comprobación de P1

Actualización del 2 de noviembre de 2026. Responsable: Marco. Revisión independiente: Diego Hurtado.

Nota del 3 de noviembre de 2026: este documento conserva las comprobaciones y pendientes de su fecha original. Los PR #45 y #46 ya fueron integrados y la recuperación del catálogo se comprobó en `main`. Para las responsabilidades actuales y el PR de API pendiente, consultar la [distribución vigente](../../references/etapa4/distribucion_actual.md) y la [comprobación de integración](cierre_api_marco_20261103.md#comprobación-tras-integrar-catálogo-y-paridad).

Los PR [#43](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/43) y [#44](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/44) fueron aprobados por Diego Hurtado e integrados en `main`. La base conjunta es `c9db414b7461cbb941ed9f79bc5dec8d3716c1a9`. Se conservan el reporte corregido de MLflow, la protección del Registry y el paquete verificable de P1 para la API. La captura original del Registry ya está incluida en la evidencia.

## Comprobaciones realizadas

| Comprobación | Resultado | Alcance |
|---|---|---|
| Integración de reproducción y servicio | 53 pruebas aprobadas, 0 fallos, 16 advertencias | Código integrado de `main`, entorno completo del proyecto. |
| Servicio con el perfil ampliado | 38 pruebas aprobadas, 0 fallos, 14 advertencias | Entorno aislado del servicio; incluye siete casos nuevos. |
| Predicción local frente al Registry | 12,096 entradas; diferencia máxima 0.0 | Misma versión numérica de P1 en proceso independiente. |
| Repetición local | Predicciones idénticas | Sin reentrenar ni recalibrar. |
| Integridad del paquete | Las huellas siguen coincidiendo | Los 22 archivos del manifiesto aprobado. |
| Aliases oficiales | P1, P2 y P3 mantienen versión 1 y sus corridas | Consulta antes y después; sin cambiar modelos ni aliases. |
| Bandit del verificador | Un aviso LOW B404; ninguno MEDIUM o HIGH | Importación de subprocess, ya justificada; no usa shell ni instrucciones de una petición. |

El código ejecutado para la paridad es `24937f7a9342927599ddf4481d497e8fea125dce`. Los resultados y el entorno constan en [validacion_ampliada_marco.json](validacion_ampliada_marco.json) y [paridad_modelo_ampliada_marco.json](paridad_modelo_ampliada_marco.json). La comprobación original de 72 entradas se conserva en su archivo anterior.

## Cobertura y límites

El perfil combina las estaciones 10, 20, 50, 100 y 200, los doce meses, los siete días de la semana y las 24 horas. Antes de predecir, se comprueba que esas cinco estaciones aparecen en las tablas ajustadas del baseline, que contienen 369 estaciones. Se añade 99999 y se comprueba que no pertenece a esas tablas para evaluar la respuesta de respaldo. Son 2,016 entradas por estación, sin filas repetidas.

Los casos son entradas artificiales de calendario. La comparación demuestra igualdad entre la carga local y la versión del Registry para estos casos; no mide error frente a viajes observados, estabilidad futura ni desempeño HTTP. El baseline seleccionado no utiliza el mes en el cálculo de sus medias: recorrer los doce meses comprueba compatibilidad de la entrada, no sensibilidad estacional. La política pública ante estaciones desconocidas corresponde al esquema y adaptador de la API.

La carga local y sus predicciones se ejecutaron con las solicitudes de `requests` bloqueadas. El proceso de referencia sí necesita acceso de lectura al Registry. Esta comprobación no acredita aislamiento de red del contenedor ni compatibilidad Linux. El paquete conserva las dependencias históricas; las advertencias de versión se mantienen visibles en la ejecución.

## Repetir la comprobación

Usar el entorno `.venv-api` y el paquete descargado conforme al manifiesto, siguiendo el README. Verificar primero que el entorno exista y que el servidor oficial esté disponible. Desde la raíz del repositorio en PowerShell:

```powershell
$pythonApi = '.venv-api\Scripts\python.exe'
$env:MLFLOW_TRACKING_URI = 'http://127.0.0.1:5000'
$env:MLFLOW_REGISTRY_URI = $env:MLFLOW_TRACKING_URI
& $pythonApi -B -m mibici_equipo39.serving.verify_model --profile extended
if ($LASTEXITCODE -ne 0) { throw 'La comparación ampliada no terminó correctamente.' }
```

La opción `extended` guarda su resultado en `reports/etapa4/paridad_modelo_ampliada_marco.json`. El perfil predeterminado sigue siendo `basic` y conserva el destino original. `--report-path` permite elegir otro archivo. Para el contenedor, Diego Hurtado debe repetir esta comprobación o su equivalente en Linux antes de declarar compatibilidad.

## Pendientes del equipo

| Actividad | Responsable | Dependencia |
|---|---|---|
| Revisar la ampliación de paridad | Diego Hurtado | Código, pruebas y resultados disponibles en el PR de esta ampliación. |
| Integrar la ampliación | Marco | Aprobación independiente de Diego Hurtado. |
| Esquemas, adaptador, ejemplos y pruebas | Stefania | Firma, cargador y manifiesto ya integrados en `main`; puede comenzar. |
| FastAPI y pruebas HTTP | Diego Martinez | Puede preparar la estructura; para inferencia real necesita los esquemas de Stefania. |
| Contenedor y validación Linux | Diego Hurtado | Puede preparar la construcción; el ensayo completo requiere API y esquemas. |
| Comprobación final desde clon limpio y evidencias HTTP | Marco y Diego Hurtado | API, esquemas y contenedor integrados y revisados. |

La consulta del catálogo `nomenclatura_2026_09.csv` volvió a devolver HTTP 404 el 2 de noviembre. La descarga completa desde cero sigue dependiendo de esa fuente externa; el empaquetado puede continuar con el modelo oficial existente. No se sustituyeron fuentes, hashes ni periodos.
