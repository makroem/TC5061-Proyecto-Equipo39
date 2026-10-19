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

Los rezagos y medias moviles permanecen fuera de la comparacion aleatoria actual y se reservan para futuras evaluaciones temporales.

---

## Aprendizaje

Se utiliza una particion aleatoria reproducible:

- Seed = 39
- Train = 70 %
- Validation = 15 %
- Test = 15 %

La particion se realiza agrupando dias completos y estratificando por mes mediante `split_manifest.json`.

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
- El candidato de P1 mejora el MAE de validacion.
- Los modelos de P2 logran metricas utiles de clasificacion.
- P3 genera grupos interpretables y evaluables.
- Todos los experimentos son reproducibles utilizando el mismo `split_id` y la misma version de datos.