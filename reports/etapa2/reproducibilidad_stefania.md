# Reproducibilidad P1
Rama: feat/stefania-a6-p1

## Pruebas
python -m pytest tests/test_stage2_p1.py -v
Resultado: 7 passed

# Ejecucion local
python -m mibici_equipo39.modeling.p1

# Ejecucion Projects
mlflow run . -e train --env-manager local --experiment-name mibici-equipo39 -P question=p1 -P member=Stefania