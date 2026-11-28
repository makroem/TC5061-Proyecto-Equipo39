# Reproducir el contraste estacional de la Etapa 5

La corrección del 25 de noviembre añade objetivo y predicción al monitoreo y compara octubre de 2025 con octubre de 2026. No reemplaza la corrida A/B, los modelos registrados ni las entregas previas. El directorio de salida es `reports/etapa5/correccion_20261125/`.

## Requisitos

Trabajar desde la raíz del repositorio con Python 3.11.9. Usar dos entornos separados: el histórico de entrenamiento (MLflow 2.22.0 y scikit-learn 1.6.1) para producir las predicciones, y Evidently 0.7.23 para los reportes. No instalar Evidently sobre el entorno del modelo.

Los datos `data/monitoring/reference.parquet`, `current.parquet` y su manifiesto deben proceder de la preparación verificada de la Etapa 5. Seguir [reproduccion.md](reproduccion.md) para obtenerlos. El paquete de A debe corresponder a `references/etapa4/model_manifest.json`; seguir [la preparación del modelo](../../README.md#etapa-4-preparación-del-modelo-para-la-api). No sustituirlo por una base de prueba ni por el CSV de estaciones. No subir datos, predicciones por fila ni el paquete binario a Git.

## Comandos

En PowerShell, activar primero el entorno histórico compatible. Indicar la carpeta real del paquete si es distinta de `models/serving/p1`:

```powershell
python -B -m mibici_equipo39.monitoring.predict_drift --model-dir models/serving/p1
```

El comando verifica el paquete antes y después, produce las predicciones sin entrenar y registra sus huellas en `private_results/etapa5/seasonal/manifest.json`. `-B` evita agregar archivos al paquete verificado.

Si aún no existe el entorno de monitoreo:

```powershell
python -m venv .venv-monitor
```

Instalar y ejecutar:

```powershell
.\.venv-monitor\Scripts\python.exe -m pip install -r requirements-monitoring-dev.txt
.\.venv-monitor\Scripts\python.exe -m pip check
$env:DO_NOT_TRACK = '1'
.\.venv-monitor\Scripts\python.exe -B -m mibici_equipo39.monitoring.seasonal
.\.venv-monitor\Scripts\python.exe -m pytest tests/monitoring --confcutdir=tests/monitoring -q
```

En Linux, usar `.venv-monitor/bin/python`. `--confcutdir` limita las fixtures a monitoreo; esta suite no requiere cargar los entornos históricos de API o entrenamiento. Los controles de las otras etapas conservan sus propios workflows.

Para repetir sin reemplazar la evidencia publicada:

```powershell
.\.venv-monitor\Scripts\python.exe -B -m mibici_equipo39.monitoring.seasonal --report-dir private_results/etapa5/revision_estacional
```

Comparar métricas y CSV, no el hash de todo el HTML: Evidently incorpora identificadores de visualización que pueden variar. El manifiesto fija huellas de datos y predicciones, protocolo, versiones y código de inferencia. La comparación estacional usa la intersección de estaciones y exige mallas horarias completas; en esta ejecución los 369 identificadores coinciden y no se excluye ninguna estación.

## Resultado y alcance

34 pruebas aprobadas: 21 previas de monitoreo y 13 nuevas; 18 advertencias conservadas. Diez corresponden a deprecaciones de dependencias y ocho a correlaciones indefinidas con variables constantes. No se interpretan correlaciones indefinidas como cero; los estadísticos de drift utilizados son finitos. Bandit: cero hallazgos en los dos módulos nuevos; esto no sustituye el análisis de las etapas anteriores. `pip check` sin incompatibilidades.

Las 274,536 predicciones actuales de A coinciden exactamente con las originales de la corrida A/B por clave y etiqueta. Se mantienen los resultados A/B originales. Ver [evidencia técnica](../../reports/etapa5/correccion_20261125/verificacion_tecnica.json), [interpretación](../../reports/etapa5/correccion_20261125/interpretacion.md) y [recomendación](../../reports/etapa5/correccion_20261125/recomendacion.md).

Las capturas muestran vistas del HTML, sin modificar valores. `target_departures` y `prediction_a` se miden con controles independientes `ValueDrift`; sus roles están explícitos en los CSV y el resumen. El resumen genérico de Evidently no registra una tarea de regresión y puede mostrar esos roles como `None`; ello no afecta los dos controles ni los cálculos de error publicados.

## Revisión del equipo

Diego Hurtado: [#83](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/83), prueba propia de integridad y revisión independiente antes de integrar. Stefania: [#84](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/84), interpretación breve. Diego Martínez: [#85](https://github.com/makroem/TC5061-Proyecto-Equipo39/issues/85), cotejo de linaje y métricas. Las tres tareas están asignadas y pendientes; no se atribuyen ejecuciones, commits ni aprobaciones todavía inexistentes. Marco puede corregir observaciones sin bloquear el avance técnico; cada integrante debe registrar su contribución real.
