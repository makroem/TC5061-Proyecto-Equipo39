# Uso de las fuentes MiBici

Se utilizaron las descargas públicas de https://mibici.net/es/datos-abiertos/ para un ejercicio académico del equipo 39. No se identificó en la página consultada una licencia específica aplicable a los CSV. La publicación como datos abiertos no permite afirmar una licencia Creative Commons concreta. La licencia MIT de este repositorio corresponde al código; no se extiende a los datos de MiBici.

Los originales permanecen localmente en data/raw y data/external. La ingesta utiliza identificador de viaje, fechas y estaciones. No conserva identificadores de usuario ni variables demográficas en los datos normalizados. Los CSV, Parquet, modelos y almacenes MLflow se excluyen de Git y de la entrega académica.

En esta máquina requests recibió HTTP 406. Los trece archivos se obtuvieron mediante los enlaces de descarga del portal oficial y después se procesaron con dataset.py. La reconstrucción desde caché es verificable por hashes; la descarga automática desde un clon limpio sigue condicionada al acceso de la fuente. No debe declararse resuelto ese requisito mientras persista el rechazo.
