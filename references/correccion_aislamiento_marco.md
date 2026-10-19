# Corrección de aislamiento y reproducción

Marco prepara esta corrección sobre el trabajo existente de Stefania y Diego Martínez. Conserva sus commits y autoría. La ingesta ya se incorporó a main mediante el PR #4, aprobado por Stefania.

El experimento con días aleatorios utiliza únicamente calendario en X. Los rezagos y medias móviles de salidas/llegadas no se entregan a P1 ni P2: un objetivo de validación o prueba podría reaparecer como predictor de otra fecha de entrenamiento. La codificación de estación de P2 conserva su ajuste exclusivamente con train. La función auxiliar de rezagos se conserva para futuros diseños temporales, pero no participa en esta evaluación.

Se conserva el rango de fechas del manifiesto de partición confirmado, incluida la fecha de inicio 2025-10-09, y su asignación actual. No se amplía el conjunto de evaluación ni se cambia el split_id como parte de esta corrección. FEATURE_SCHEMA_VERSION pasa a 5-random-calendar-only; deben regenerarse las tablas derivadas y repetirse las métricas de P1 y P2. Las métricas y figuras anteriores corresponden a la versión previa, no acreditan los resultados corregidos.

Al construir variables se lee y compara íntegramente split_manifest.json con la partición reproducida. Una discrepancia o un manifiesto ausente detiene la ejecución sin escribirlo. Las nuevas particiones deben generarse, versionarse y revisarse explícitamente por PR.

Las pruebas de regresión alteran exclusivamente objetivos de días reservados y comprueban que no cambien las variables usadas en entrenamiento. También comprueban que un manifiesto distinto sea rechazado y conservado sin cambios.

P3 y el controlador final de seis experimentos siguen pendientes de la aportación y revisión de Persona4. Esta corrección no los sustituye ni acredita la reproducción independiente de los cuatro integrantes.
