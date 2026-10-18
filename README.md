# TC5061 Proyecto Equipo 39

## Propósito
Proyecto académico MiBici para estudiar demanda por estación, presión de flujo y grupos de uso. Esta rama contiene la estructura y la ingesta de Marco. La integración de los módulos del equipo y su ejecución oficial siguen pendientes.

## Integrantes y roles
Marco (makroem, identificador técnico persona1) prepara configuración, ingesta, versionado y coordinación. Stefania (a01236059-lab, persona2) implementa variables, partición, P1 y Canvas. Diego Martinez (Sanciprian, persona3) implementa P2. Diego Hurtado (invitación pendiente para diegoHurtado01, persona4) implementa P3, Tracking y propuesta final. Estas asignaciones no acreditan contribuciones o revisiones todavía no realizadas.

## Preguntas y usuarios
P1 regresión: viajes que se iniciarán por estación en la próxima hora; la usa el operador para planear la flota. P2 clasificación: riesgo aproximado de falta de bicicletas o anclajes en la próxima hora, usando capacidad publicada; la usa rebalanceo. P3 clustering: grupos de estaciones con patrones semejantes y sus coordenadas; lo usa planeación urbana y expansión. P2 es una aproximación sin inventario observado. Ver references/ingesta_interface.md.

## Fuentes y tamaño
Doce meses de octubre de 2025 a septiembre de 2026. 4497877 filas originales y 4497119 viajes completos retenidos. 484 estaciones en catálogo y 480 con capacidad válida. 390347882 bytes descargados. Fuentes y hashes: references/data_manifest.json. Detalle mensual: reports/calidad_datos_por_mes.csv.

## Licencia y privacidad
Código con licencia MIT de la plantilla. No se atribuye a los CSV una licencia no identificada. No se publican los archivos de MiBici ni datos de usuario. Ver references/data_usage.md.

## Estructura
data contiene solo marcadores en Git; mibici_equipo39 contiene módulos; notebooks contiene exploración; references contiene manifiestos y contratos; reports contiene agregados; models no contiene modelos serializados. La estructura se generó con ccds 2.3.0 y scaffold Yes. Los archivos de plantilla pendientes de reemplazo no son una solución final.

## Instalación
Comprueba primero Python 3.11.9 y Git con sus comandos de versión. Si ya están disponibles, reutilízalos. Desde la raíz crea un entorno con python -m venv .venv y, en Windows, ejecuta .venv\Scripts\python.exe -m pip install -r requirements.txt. En Linux o Colab utiliza .venv/bin/python. El lock fija dependencias y marca pywin32 como exclusivo de Windows. Las fechas y la semilla están centralizadas en config.py.

## Ingesta y verificación
Ejecuta python -m mibici_equipo39.dataset --freeze-manifest solo para la versión inicial autorizada. Para reproducir el manifiesto confirmado ejecuta python -m mibici_equipo39.dataset --verify-manifest. En esta máquina la descarga Python recibió HTTP 406; se descargaron las trece fuentes desde https://mibici.net/es/datos-abiertos/ a data/raw y data/external antes de procesar. La descarga automática desde un clon limpio debe revalidarse.

## Variables y pruebas
Las pruebas de Persona1 se ejecutan con python -m pytest tests/test_data.py -v. El notebook notebooks/1.0-p1-auditoria-ingesta.ipynb contiene resultados de la auditoría local. Features y la partición oficial esperan la integración de Persona2; el módulo de plantilla no se debe ejecutar como implementación final. La referencia usa días aleatorios estratificados por mes, seed 39, proporciones aproximadas 70/15/15.

## Experimento y MLflow Projects
La implementación completa de referencia se entrega por separado para revisión. Sus ejecuciones usan mibici-equipo39-referencia y executor persona1. El experimento oficial mibici-equipo39 y el comando mlflow run . --env-manager=local esperan los módulos, manifiestos y MLproject integrados. No hay todavía evidencia de ejecución oficial desde main.

## Flujo Git y GitHub
Ramas chore/persona1-estructura y feat/persona1-ingesta publicadas el 17 de octubre de 2026. PR de estructura: https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/1. PR de ingesta: https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/2. Ambos solicitan revisión a Stefania. main está protegida con PR, una aprobación, descarte de aprobaciones antiguas y conversaciones resueltas; se bloquean force push y eliminación, también para administradores.

La base provisional del PR de ingesta es chore/persona1-estructura para mostrar solo los cambios adicionales. Primero incorporar el PR de estructura con merge commit después de su aprobación; después cambiar la base del PR de ingesta a main y volver a comprobar diferencias y revisiones. No incorporar la ingesta en la rama de estructura. Su aprobación final también depende de resolver la descarga automática. Convención de commits chore, feat, fix y docs. Ver references/colaboracion.md.

## Resultados limitaciones y evidencia
Ingesta y notebook locales verificables; la reproducción oficial y las evidencias colaborativas están pendientes. La partición aleatoria no mide pronóstico sobre un periodo posterior. El catálogo de capacidad es de septiembre de 2026 y no representa inventario observado. La propuesta debe justificar herramientas con las lecturas del curso y confrontar el criterio temporal de la rúbrica.

Buenas prácticas: config.py centraliza configuración; requirements.txt fija versiones; .gitignore excluye datos, modelos, credenciales y MLflow; data_manifest.json versiona fuentes y salidas; el flujo de PR y las etiquetas oficiales se verificarán cuando exista integración. No se deben presentar pruebas sintéticas ni runs de referencia como resultados oficiales del equipo.
