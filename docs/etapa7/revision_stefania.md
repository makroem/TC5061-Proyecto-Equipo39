# Revisión de Model Card y explicación de drift

Se revisó el documento docs/etapa7/model_card.md considerando su uso previsto, limitaciones declaradas y consistencia con la evidencia referenciada. El uso previsto se encuentra claramente delimitado en la sección "Uso y alcance", donde se establece que el servicio estima viajes observados por estación y hora para apoyar actividades de redistribución de bicicletas y que no debe utilizarse para decisiones sobre personas, ingresos, demanda insatisfecha ni estaciones sin historial comprobado.

De igual manera, verifican además dos limitaciones relevantes, la primera es que octubre de 2025 forma parte del entrenamiento del modelo A, por lo que las métricas obtenidas para ese periodo no constituyen una evaluación independiente de generalización. La segunda es que los viajes observados dependen de factores operativos no incluidos explícitamente en el modelo, como disponibilidad de bicicletas, horarios de operación y posibles cierres, por lo que los resultados deben interpretarse con cautela y no permiten inferir causalidad.

También se validó la consistencia de la explicación estacional incorporada a partir de la evidencia de reports/etapa5/correccion_20261125/interpretacion.md y reports/etapa5/correccion_20261125/resumen.json. La distinción entre el crecimiento interanual de la demanda (38.00 %) y la subestimación agregada del modelo (36.83 %) se encuentra correctamente documentada y utiliza denominadores diferentes, evitando interpretaciones incorrectas.


