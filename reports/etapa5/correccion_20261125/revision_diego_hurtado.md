# Revision independiente de la correccion estacional

**Responsable:** Diego Hurtado
**Fecha:** 26 de noviembre de 2026
**Proyecto:** TC5061-Proyecto-Equipo39 (MiBici)
**Tarea:** #83
**Pull request revisado:** #86
**Commit revisado:** a2f5122beb58c1895adcd5c86d633b0a32936871

## 1. Objetivo y alcance

Realizar una revision independiente de la correccion del monitoreo
de drift de demanda y prediccion, verificando las pruebas
automatizadas, la integridad del manifiesto de predicciones,
los resultados numericos y la evidencia grafica publicada.

La revision se realizo sobre una rama independiente creada
desde el commit indicado del PR #86.

No se modificaron las mediciones originales, los modelos A/B,
el champion ni los resultados historicos.

## 2. Entorno y pruebas automatizadas

- Sistema operativo: Windows.
- Python: 3.11.9.
- pytest: 9.0.3.
- Dependencias: requirements-monitoring-dev.txt.
- Entorno virtual: MiBici/venv-monitor, fuera del repositorio.

Comando utilizado:

```powershell
python -m pytest tests/monitoring --confcutdir=tests/monitoring -q
```

Resultados de la ejecucion original, antes de agregar pruebas:

- 34 pruebas aprobadas.
- 0 pruebas fallidas.
- 18 advertencias.
- Duracion: 8.25 segundos.

Resultados posteriores a incorporar la prueba independiente:

- 36 pruebas aprobadas.
- 0 pruebas fallidas.
- 18 advertencias.
- Duracion: 4.33 segundos.

Las advertencias incluyen interfaces obsoletas de dependencias
y operaciones numericas indefinidas durante algunas pruebas.
No ocasionaron fallos, pero deben mantenerse bajo observacion.

## 3. Prueba independiente de integridad

Se creo el archivo:

`tests/monitoring/test_revision_diego_hurtado.py`

La prueba parametrizada evalua dos alteraciones controladas:

1. Sustitucion de la version declarada del modelo.
2. Sustitucion del SHA-256 declarado para el paquete del modelo.

Primero se comprueba que un manifiesto con identificadores
aprobados supera el control inicial del linaje.

Posteriormente se introduce cada alteracion de forma aislada
y se verifica que el sistema rechace el manifiesto mediante
ValueError.

Resultado: 2 pruebas independientes aprobadas.

El control utiliza archivos temporales y un reemplazo controlado
de la funcion de carga posterior. Por ello, comprueba el rechazo
del linaje alterado, pero no la integridad completa de los
archivos Parquet ni la ejecucion integral del modelo.

## 4. Verificacion numerica

Se revisaron `resumen.json`, `drift_historico_variables.csv`
y `drift_estacional_variables.csv`.

Se recalcularon los siguientes indicadores desde los promedios
publicados, contrastandolos con una tolerancia de 0.0001 puntos
porcentuales:

| Indicador | Resultado |
|---|---:|
| Crecimiento historico | 58.3116 % |
| Crecimiento estacional | 38.0021 % |
| Crecimiento estandarizado | 39.7295 % |
| Subestimacion agregada de A | 36.8311 % |

Todos los indicadores coincidieron dentro de la tolerancia.

Se verifico tambien la clasificacion de drift:

| Comparacion | Entradas evaluadas | Entradas con drift | Objetivo | Prediccion |
|---|---:|---:|---|---|
| Historica | 9 | 3 | Drift | Sin drift |
| Estacional | 9 | 0 | Drift | Sin drift |

El denominador de entradas se mantiene en nueve.
Las alertas del objetivo y la prediccion se evalúan
separadamente.

## 5. Verificacion de reportes y capturas

Se abrieron localmente los reportes:

- `drift_estacional.html`
- `drift_historico.html`

Se comprobaron los SHA-256 y tamanos de las cinco capturas
contra `capturas/manifiesto.json`.

Resultado: 5 de 5 archivos coincidentes.

En las secciones visibles de los reportes se confirmaron:

| Variable | Historico | Estacional |
|---|---:|---:|
| target_departures | 0.323 | 0.219 |
| prediccion_a | 0.006 | 0.007 |

Los valores son distancias de Wasserstein normalizadas,
presentadas aqui con tres decimales.

El objetivo presenta drift en ambas comparaciones,
mientras que la prediccion no presenta alerta.

Se verifico la coherencia de estas secciones visibles
con los resultados tabulares. La comprobacion de huellas
de las cinco capturas no equivale a una inspeccion visual
exhaustiva de todas las graficas.

## 6. Interpretacion y limitaciones

El contraste estacional muestra un aumento de la demanda
observada y una distribucion de predicciones relativamente
estable.

Esto es consistente con la subestimacion agregada del
modelo A en octubre de 2026.

Sin embargo:

- No se reentrenaron los modelos A ni B.
- No se sustituyo ni promovio ningun modelo.
- No se reprodujo desde cero el calculo completo de Evidently
  sobre los archivos Parquet.
- No se audito la integridad completa del paquete del modelo.
- La revision visual se limita a las secciones observadas
  en los reportes y capturas disponibles.
- Las 18 advertencias de pytest no se resolvieron.
- La ausencia de drift de prediccion no demuestra buena
  calidad predictiva.
- No se demuestra concept drift ni causalidad del aumento
  de demanda con una sola comparacion interanual.

## 7. Conclusion

Las 36 pruebas automatizadas finalizaron correctamente,
incluidas las dos pruebas adicionales de integridad.

Los cuatro porcentajes verificados coincidieron con los
resultados publicados. La clasificacion del drift mantiene
nueve entradas y alertas independientes para demanda y
prediccion. Las cinco capturas superaron las comprobaciones
de integridad SHA-256.

No se identificaron inconsistencias bloqueantes dentro
del alcance efectivamente verificado.

La revision tecnica de estas evidencias es favorable.
La aprobacion formal del PR #86 se realizara tras publicar
esta contribucion, comprobar su integracion y revisar
el ultimo commit del PR.

**Autor de esta revision:** Diego Hurtado.
