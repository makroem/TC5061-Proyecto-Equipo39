# Capturas del ensayo de migración

Capturas directas de la interfaz de MLflow 3.17.2, obtenidas por Marco el 28 de octubre de 2026. Corresponden a la copia migrada del almacén, servida localmente en el puerto 5001. No son capturas de un cambio aplicado al servidor oficial.

- `registry_migrado.png`: los tres modelos conservan su versión 1 y el alias `champion`.
- `corridas_conservadas.png`: el experimento `mibici-equipo39` mantiene 34 corridas, incluidas búsquedas y reproducciones anteriores.

Se utilizó la vista de entrenamiento, con la barra lateral contraída. En la tabla se desactivó la columna de ruta local mediante el selector de columnas. No se editaron píxeles ni se modificaron las corridas. Las capturas complementan la comprobación de hashes, contenido SQLite y predicciones; por sí solas no prueban toda la migración.
