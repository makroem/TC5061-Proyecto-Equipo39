"""Estimación de costo por inferencia útil con supuestos explícitos."""
import math

def estimate(monthly_usd, successful_predictions, duration_seconds, utilization=1.0, hours_per_month=730.0):
    values=(monthly_usd, successful_predictions, duration_seconds, utilization, hours_per_month)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):
        raise ValueError('Los valores deben ser números finitos.')
    if monthly_usd < 0 or successful_predictions <= 0 or duration_seconds <= 0 or hours_per_month <= 0:
        raise ValueError('Costo no negativo, tiempo e inferencias positivos.')
    if not 0 < utilization <= 1:
        raise ValueError('La utilización debe estar entre cero exclusivo y uno.')
    rate=successful_predictions/duration_seconds
    capacity=rate*hours_per_month*3600*utilization
    return {'monthly_usd':monthly_usd, 'hours_per_month':hours_per_month,
            'successful_predictions_per_second':rate, 'utilization':utilization,
            'estimated_monthly_predictions':capacity, 'usd_per_prediction':monthly_usd/capacity,
            'usd_per_1000_predictions':1000*monthly_usd/capacity,
            'allocated_test_usd':monthly_usd*duration_seconds/(hours_per_month*3600)}
