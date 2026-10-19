# Datos de Persona1

## Fuente y periodo
Doce CSV mensuales de octubre de 2025 a septiembre de 2026 y nomenclatura_2026_09.csv. Inicio inclusivo 2025-10-01 y fin exclusivo 2026-10-01. Fuente: https://mibici.net/es/datos-abiertos/.

## Tamaño medido
Filas originales 4497877; viajes completos retenidos 4497119; duplicados excluidos 758; catálogo 484 estaciones; unión de estaciones observadas en salidas y llegadas 471; capacidades válidas 480. Total descargado 390347882 bytes. Parquet de viajes, eventos y catálogo 252742436 bytes. Ver reports/calidad_datos_por_mes.csv para cifras por mes y cobertura de estaciones desconocidas.

## Variables y limpieza
trip_id, started_at, ended_at, origin_id y destination_id. Catálogo station_id, station_name, latitude, longitude, capacity, valid_capacity y valid_coordinates. Timestamp local interpretado en America/Mexico_City. Se detectan duplicados globales por trip_id y contenido; un ID con contenido contradictorio detiene el proceso. Las exclusiones son mutuamente excluyentes y se concilian con las filas originales. Se conservan salidas con inicio válido sin utilizar la hora futura de finalización como requisito. Las llegadas requieren un viaje completo coherente.

## Versionado
data_version e9de13df5e9bdc1fde98c042f700e1a7c568ad85df5a303a96a78b3d4d45dbb7. references/data_manifest.json contiene URL, bytes, SHA256 y codificación de las trece fuentes y hashes lógicos de los archivos normalizados. --freeze-manifest congela una versión; --verify-manifest reconstruye y exige igualdad exacta. No actualizar el manifiesto para ocultar cambios inesperados.

## Partición y límites
Config.py fija seed 39 y proporciones train 0.70, validation 0.15 y test 0.15. features.py asigna días completos al azar dentro de cada mes, redondeando los cortes acumulados de 70% y 85%: 252 días de train, 52 de validación y 53 de prueba. El mapa común a P1, P2 y P3 y su split_id están en split_manifest.json; la construcción lo verifica y se detiene ante cualquier diferencia. No comparte días entre conjuntos. Se omite el 1 de octubre de 2025 por falta de eventos del mes anterior; esta decisión no elimina todas las limitaciones de borde para viajes largos.

La partición aleatoria mezcla fechas y evalúa datos reservados del mismo año, sin demostrar generalización a meses futuros. Se usan variables de calendario; los rezagos quedan fuera de esta comparación. La capacidad procede de un catálogo de septiembre de 2026 y no acredita la capacidad histórica. Debe declararse el posible conflicto con el criterio temporal de la rúbrica. Las lecturas institucionales y su justificación corresponden al documento final del equipo y siguen pendientes de consulta.
