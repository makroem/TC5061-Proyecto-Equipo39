# Revisión de las seis verificaciones de operación

Tarea #76. Revisó Diego Martinez el 22 de noviembre de 2026, sobre `main` en `19a0e0a`. Contrasta las
[seis verificaciones de Marco](verificacion_documental.md) con el README, `docker-compose.yml` y las
evidencias publicadas, y repite en mi equipo lo que se puede ejecutar sin el paquete original de P1.

Equipo: macOS ARM, Docker 29.2.0 con motor Linux arm64 y Python 3.11.9 en un entorno nuevo instalado
desde `requirements-api-dev.txt`. No tengo el paquete de P1 versión 1, así que el despliegue usó la
fixture sintética del flujo de CI (`python -B -m scripts.create_ci_model`) con `MODEL_PATH` y
`MODEL_MANIFEST_PATH`, igual que GitHub Actions.

## Verificaciones

| # | Punto | Resultado | Cómo se comprobó | Observación |
|---|---|---|---|---|
| 1 | Comando único de inicio | Conforme, ejecutado | `docker compose config --quiet` sin errores. Construcción y arranque en dos pasos, como en CI: `docker compose build` (unos 4 minutos la primera vez) y `docker compose up -d --wait --wait-timeout 300`. `api` y `mlflow` quedaron `healthy`. | Funciona igual en macOS ARM. Según `docker-compose.yml`, sin paquete en `models/serving/p1/` el montaje falla porque no crea la carpeta. |
| 2 | Dirección de `/ready` | Conforme, ejecutado | `http://127.0.0.1:8006/ready` respondió 200 con `status: ready`, nombre, versión y huella. `/health` respondió 200 y el tracking en `http://127.0.0.1:5006/health` también. | El puerto cambia con `API_PORT`. El 8000 sigue siendo el del ejemplo aislado de Etapa 4. |
| 3 | Ejemplo de predicción | Conforme en formato. Valor de P1 solo revisado | Con el [ejemplo versionado](../../references/etapa4/examples/predict_request.json), `/predict` respondió 200 con el esquema esperado. `mibici_equipo39.operations.smoke` aprobó lotes de 1, 10 y 100, y 422 con lista vacía. | La fixture devuelve 1.0. El valor 1.6764705882352942 de P1 no lo pude repetir sin el paquete; coincide en el README, `predict_response.json` y la captura E05. |
| 4 | Persistencia | Conforme, ejecutado | `tracking_check write`, después `docker compose down` y `up -d --wait`, y al final `tracking_check read`: "Persistencia verificada". El volumen `e39-etapa6_tracking` se conservó tras el `down`. | Es más estricta que la prueba de CI, que solo recrea `mlflow`. `docker compose down -v` borraría el registro. |
| 5 | Flujo exitoso | Conforme, consultado | Con `gh run view`, la [ejecución 44553281639](https://github.com/makroem/TC5061-Proyecto-Equipo39/actions/runs/44553281639) sobre `7c49a81` terminó `success` en sus tres trabajos: pruebas en Windows, pruebas en Linux y `build-deploy`. También la 44981895636 sobre `1359830` y la última de `main`, sobre `19a0e0a`. | En mi equipo, `pytest tests/api tests/operations` dio 108 aprobadas, la misma cifra por entorno que reporta CI. |
| 6 | Gráficas y archivos de origen | Conforme, ejecutado | Regeneré las tres gráficas con `scripts/plot_load.py` en una carpeta temporal, desde `performance.csv`, `resources.csv` y `locust/u30_r1.json`. `rendimiento_latencia.png` y `recursos.png` son idénticas byte a byte. En la serie de Locust ningún píxel cambia más de 1 nivel de 255. | Las medianas de p95 recalculadas son 51, 460 y 1,700 ms, con 13,001 solicitudes y 0 fallos, igual que en el reporte. |

## Qué se ejecutó y qué solo se revisó

Se ejecutaron los puntos 1, 2, 4 y 6, el formato del punto 3 y las 108 pruebas. Solo se revisaron,
sin ejecutarlos: la predicción con P1 real, los comandos de PowerShell y las mediciones de carga, que no
repetí con Locust. Los resultados de mi ejecución quedaron en `private_results/etapa6/`, fuera de Git.

## Observaciones

1. Los comandos para comprobar la Etapa 6 solo estaban en PowerShell. Agregué al README el equivalente
   con `curl` para macOS y Linux.
2. Sin acceso al Registry, el README no decía cómo probar el despliegue. Agregué una línea con la
   fixture de CI y las dos variables, aclarando que responde `ci-fixture-only` y no P1.
3. `plot_load.py` escribe las gráficas en la misma carpeta que lee. Si se corre sobre
   `references/etapa6/mediciones_marco` reemplaza las publicadas, así que conviene usar una copia.

No encontré discrepancias con las seis verificaciones de Marco. Esta revisión no cambia datos, modelos,
mediciones ni resultados.
