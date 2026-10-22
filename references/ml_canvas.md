# ML Canvas - Proyecto MiBici Equipo 39

## Propuesta de valor

Apoyar la planeacion de flota, la priorizacion de rebalanceo y el analisis de patrones de estaciones.

---

## Tarea de ML

- P1: Regresion de conteos.
- P2: Dos clasificaciones binarias de presion.
- P3: Clustering de perfiles.

---

## Datos

Viajes de octubre de 2025 a septiembre de 2026 y nomenclatura de estaciones con capacidad y coordenadas.

---

## Predicciones

- Conteo esperado por estacion y hora.
- Dos puntajes proxy de riesgo.
- Grupo o perfil de estacion.

---

## Decisiones

- Distribuir recursos.
- Revisar estaciones con alertas.
- Estudiar cobertura y expansion del sistema.

---

## Usuarios

- Operador del sistema.
- Equipo de rebalanceo.
- Equipo de planeacion urbana.

---

## Evaluacion Offline

### P1
- MAE
- RMSE

### P2
- Recall
- Precision
- F1
- Average Precision (AP)

### P3
- Silhouette
- Davies-Bouldin
- Estabilidad ARI

---

## Recoleccion

- Descarga mensual automatica.
- Validacion de esquema.
- Manifiesto SHA-256.
- Control de versiones de datos.

---

## Construccion de Variables

Variables activas:

- hour_of_day
- day_of_week
- month
- is_weekend
- hour_sin
- hour_cos
- month_sin
- month_cos

Se utilizan ciclos temporales de hora y mes.

Los rezagos y medias moviles permanecen fuera de esta comparacion. P1/P2 utilizan solo calendario conocido al predecir. P3 usa 48 perfiles horarios (laborales y fin de semana), normalizados por tipo de dia, y StandardScaler ajustado solo con train; las coordenadas se unen despues para el mapa.

---

## Aprendizaje

Se utiliza una particion cronologica confirmada, con semilla de modelos 39:

- Train: octubre de 2025 a mayo de 2026, 243 dias.
- Validation: junio y julio de 2026, 61 dias.
- Test: agosto y septiembre de 2026, 61 dias.

La particion respeta dias completos y fechas contiguas mediante `split_manifest.json`. Se conserva el manifiesto aleatorio anterior solo como historial. Test no participa en elegir modelo o umbral. Los grupos de P3 describen el perfil historico; su estabilidad temporal se evalua por separado. El catalogo de septiembre no constituye un inventario observado ni un registro historico de capacidades.

---

## Monitoreo

No existe monitoreo desplegado en esta entrega.

A futuro se recomienda monitorear:

- Cambios de esquema.
- Valores faltantes.
- Deriva de datos.
- Deriva de desempeño.

---

## Criterio de Exito

- Baselines reproducibles y ejecutables.
- P1 selecciona por menor val_mae (empate baseline); MAE/RMSE de test se reportan sin reajustar. Una falta de mejora se informa objetivamente.
- P2 selecciona por val_macro_f1 y declara precision/recall/AP y falsas alertas. Un recall alto del proxy no demuestra utilidad operativa ni falta real de bicicletas.
- P3 compara KMeans y GMM k=3 por val_silhouette, con grupos train de al menos 5%; evalua Davies Bouldin y ARI de cinco remuestreos train. Si ningun modelo cumple se declara. Interpretacion urbana y efecto operativo requieren validacion adicional.
- Todos los experimentos son reproducibles utilizando el mismo `split_id` y la misma version de datos.
