# Contrato de la ingesta

Ejecutar desde la raíz del proyecto con Python 3.11.9:

```text
python -m mibici_equipo39.dataset --freeze-manifest
python -m mibici_equipo39.dataset --verify-manifest
python -m pytest tests/test_data.py -v
```

Entradas: las URLs centralizadas en config.py, doce CSV en data/raw y catálogo en data/external. Los archivos existentes se reutilizan; en modo verify su SHA256 debe coincidir. Salidas: data/processed/stations.parquet, data/processed/trips/month=AAAA-MM/part-*.parquet, data/interim/departures y data/interim/arrivals con station_id y timestamp. Las claves de estación son cadenas; no convertirlas a índices numéricos por posición.

Persona2 necesita el manifiesto aprobado y estos Parquet para construir variables y el mapa de días. Persona3 debe utilizar capacity y valid_capacity; no imputar una capacidad fija. Persona4 necesita el mismo data_version y después el split_id aprobado. Los eventos de estaciones ausentes en el catálogo se conservan en ingesta y se excluyen de los modelos de estación que requieren ese catálogo; sus conteos están en el reporte mensual.

P2 aproxima presión de flujo: ocupación hipotética inicial 0.5 por capacidad, bicicletas en riesgo si el mínimo intrahorario llega a 0.1 por capacidad o menos, anclajes en riesgo si el máximo llega a 0.9 por capacidad o más. No se etiqueta el estado real observado. Persona3 debe revisar las dos salidas binarias, las clases raras y la sensibilidad a ocupación inicial 0.25 y 0.75.
