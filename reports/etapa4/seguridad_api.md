# Revisión de seguridad del arranque de la API

Responsable: Marco. Fecha: 2 de noviembre de 2026.

## Alcance y resultados

Se revisó `mibici_equipo39/serving/` con Bandit 1.9.4 y las 67 dependencias fijadas en `requirements-api.txt` con pip-audit 2.10.1. Se conservaron los reportes JSON originales, con rutas relativas:

- [Bandit](bandit_api.json): un aviso LOW B404, ninguno MEDIUM/HIGH; código de salida 1 por ese aviso.
- [pip-audit](pip_audit_api.json): cero vulnerabilidades conocidas en los paquetes auditados; código de salida 0.
- `pip check`: código 0, sin dependencias incompatibles en el entorno aislado.

No se aplicaron exclusiones de vulnerabilidades. La auditoría usa `--no-deps --disable-pip` porque los requisitos contienen el conjunto transitivo fijado que se instaló y verificó. Esto no agrega protección contra vulnerabilidades aún desconocidas ni analiza el sistema operativo de la imagen futura.

## Aviso B404 y proceso de comparación

`verify_model.py` importa subprocess para cargar por separado la versión del Registry. El proceso usa el intérprete actual, código fijo incluido en el módulo, `shell=False`, un tiempo máximo de 180 segundos y archivos temporales controlados. El URI se construye a partir del manifiesto validado; no se recibe desde una solicitud HTTP. Este módulo es una utilidad de comprobación, no un endpoint.

Se considera un uso acotado del proceso; se conserva B404 visible para la revisión de Diego Hurtado. La línea de ejecución tiene una justificación localizada de B603 por estos mismos controles. No hay exclusión global de reglas ni ejecución de comandos enviados por clientes.

## Archivos y modelo

El cargador compara todos los archivos, rechaza faltantes, adicionales, cambios, enlaces simbólicos, rutas que salgan del paquete y divergencias de firma/run antes de deserializar. El manifiesto debe proceder del repositorio revisado: cambiar a la vez un modelo y sus hashes podría eludir una mera comprobación de integridad. Solo se debe preparar desde el Registry autorizado.

Se verificó que `.gitignore` excluye `models/serving/p1/MLmodel`, `.venv-api/`, `.env`, `mlflow.db`, `mlruns/` y `mlartifacts/`. `git ls-files models/serving` no devuelve modelos versionados. También quedan excluidos temporales y resultados privados. Las reglas existentes ya son suficientes; no fue necesario sustituirlas.

## Límite del cierre actual

Faltan la API de Diego Martinez, el contrato implementado por Stefania y la imagen de Diego Hurtado. Deben comprobarse allí errores HTTP sin trazas, ejecución sin privilegios, contexto sin credenciales y dependencias en Linux. Esta revisión inicial no los da por resueltos.
