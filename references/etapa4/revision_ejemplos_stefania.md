# Revisión de ejemplos de la API

## Objetivo
Verificar que el ejemplo de solicitud incluido en el repositorio sea consistente con las reglas definidas en el contrato de la API y documentar ejemplos de solicitudes válidas e inválidas.

## Resumen de validaciones 
- station_id debe ser un texto de 1 a 6 dígitos sin ceros iniciales.
- hour_of_day debe estar en el rango de 0 a 23.
- day_of_week debe estar en el rango de 0 a 6.
- month debe estar en el rango de 1 a 12.
- is_weekend debe ser coherente con day_of_week
- La API utiliza validación estricta y rechaza calendarios incoherentes.
- Las solicitudes inválidas deben responder con HTTP 422.

## Caso de validación 1: Solicitud válida

Validación:
{
  "instances": [
    {
      "station_id": "10",
      "hour_of_day": 6,
      "day_of_week": 0,
      "month": 1,
      "is_weekend": 0,
      "hour_sin": 1.0,
      "hour_cos": 0.0,
      "month_sin": 0.5,
      "month_cos": 0.8660254037844386
    }
  ]
}

Revisión:
- station_id tiene formato válido.
- hour_of_day se encuentra dentro del rango permitido.
- day_of_week se encuentra dentro del rango permitido.
- month se encuentra dentro del rango permitido.
- is_weekend es consistente con day_of_week = 0 (lunes).
- Se incluyen todos los campos requeridos por el contrato.
- No existen campos adicionales.

Resultado esperado:
La solicitud es aceptada y se produce la respuesta HTTP 200 ok

## Caso de validación 2: Hora inválida
validación:
{
  "instances": [
    {
      "station_id": "10",
      "hour_of_day": 24,
      "day_of_week": 0,
      "month": 1,
      "is_weekend": 0,
      "hour_sin": 1.0,
      "hour_cos": 0.0,
      "month_sin": 0.5,
      "month_cos": 0.8660254037844386
    }
  ]
}

Resultado esperado:
Ya que se establece que  hour_of_day debe tener valor entre 0 y 23 se espera ver HTTP 422 Unprocessable Entity


## Caso de validación 3: Calendario incoherente

validación:
{
  "instances": [
    {
      "station_id": "10",
      "hour_of_day": 6,
      "day_of_week": 0,
      "month": 1,
      "is_weekend": 1,
      "hour_sin": 1.0,
      "hour_cos": 0.0,
      "month_sin": 0.5,
      "month_cos": 0.8660254037844386
    }
  ]
}

Resultado esperado:
El contrato indica que is_weekend debe ser 1 únicamente cuando day_of_week corresponde a sábado (5) o domingo (6). En esta validación day_of_week= 0 (lunes) y is_weekend = 1 (si), por lo tanto el calendario es incoherente.
Se espera obtener un HTTP 422 Unprocessable Entity

## Limitaciones
- La revisión de los tres caso se realizó a partir del ejemplo contenido en predict_request.json y las reglas documentadas en contrato_api.md.
- No se evaluaron escenarios adicionales fuera de los casos solicitados, como identificadores de estación inválidos, meses fuera de rango, valores cíclicos inconsistentes o tipos de datos incorrectos.
- La revisión confirma la coherencia entre la documentación y los ejemplos analizados, pero no sustituye las pruebas completas de integración, rendimiento o despliegue del servicio.

## Conclusión
La solicitud de ejemplo incluida en el repositorio es válida conforme al contrato de la API. Las validaciones documentadas permiten detectar tanto horas fuera de rango como inconsistencias en los datos de calendario, respondiendo con HTTP 422 cuando la entrada no cumple las reglas definidas.



