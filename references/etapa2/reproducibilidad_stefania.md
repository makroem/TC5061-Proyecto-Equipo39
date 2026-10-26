# Reproducibilidad P1
Rama: feat/stefania-a6-p1

## Pruebas
python -m pytest tests/test_stage2_p1.py -v
Resultado: 5 passed

# Ejecucion local
python -m mibici_equipo39.modeling.p1

# Ejecucion Projects
python -m mlflow run . -e p1 -P member=Stefania --env-manager local --experiment-name mibici-equipo39