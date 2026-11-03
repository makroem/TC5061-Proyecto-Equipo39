# Recuperación del catálogo histórico

Fecha: 3 de noviembre de 2026. Implementación: Marco. Revisión: Diego Hurtado.

La consulta directa a https://mibici.net/es/datos-abiertos/ devolvió como catálogo publicado `nomenclatura_2026_10.csv`. La descarga de septiembre con la identificación HTTP del proyecto devuelve 404. Octubre responde 200, contiene 470 filas y tiene una huella distinta; no se adoptó como sustituto del catálogo histórico.

Se localizó y respaldó la copia original de septiembre fuera del repositorio. La ejecución real de `python -B -m mibici_equipo39.prepare_catalog`, con `MIBICI_SOURCE_CACHE` configurada, recuperó el archivo en `data/external/` y confirmó:

- 484 estaciones, 40,841 bytes, UTF-8 con BOM y separador coma.
- SHA256: `206e45fe633922b634d858142fa21e6fd9f4c421b6435c02980ef290cc2df90d`.
- Coincidencia exacta con `references/data_manifest.json`.
- Recuperación: `verified_cache`.

Se ejecutaron `tests/test_download.py`, `tests/test_data.py`, `tests/test_ingesta_calidad.py` y `tests/test_station_manifest.py`: **51 pruebas aprobadas, 0 fallos, 14 advertencias**, en 15.67 segundos. Cubren descarga HTTP, respaldo local, fuente HTTPS alternativa, rechazo de hashes diferentes, limpieza de archivos parciales y repetición de la ingesta sintética. La primera ejecución encontró errores de preparación porque faltaba la carpeta padre de temporales; se creó y la suite se repitió completa.

La fuente HTTPS alternativa se comprobó con respuestas controladas. Aún no se ha publicado el respaldo en un almacenamiento compartido ni comprobado su descarga remota real. El operador debe configurar esa ubicación antes de declarar reproducible la descarga desde una máquina sin la copia histórica. No se afirma haber repetido en esta validación la ingesta real de los doce meses ni el entrenamiento.

El manifiesto, las selecciones y los modelos oficiales no se modificaron. La ingesta en modo `verify` acepta exclusivamente la huella ya registrada. El CSV no se incorpora al repositorio.
