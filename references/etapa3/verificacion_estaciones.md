# Verificación del catálogo y seguimiento del entorno DeepChecks

Marco realizó esta comprobación el 31 de octubre de 2026, después del aviso de
Diego Martinez en el [PR #35](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/35).
El objetivo fue confirmar el resultado en Windows y preparar una comparación que
permita localizar la diferencia observada en macOS.

## Resultado en Windows

Las 484 estaciones coinciden con el manifiesto. El CSV original conserva el SHA256
publicado y su reconstrucción produce los mismos valores y tipos que el Parquet
local. El hash lógico del catálogo es
`84ed1ce13b7034edadd13cf0d5ae5d2fe8fd05eaa2c8d1bca9b1a130427f548e`.

Se comprobó con pandas 2.2.3 y PyArrow 23.0.1 en dos entornos: NumPy 2.1.3 para el
proyecto y NumPy 1.26.4 para DeepChecks. Ambos producen el mismo resultado, incluido
el hash por columna. En el entorno DeepChecks se verificaron además las 151 salidas
del manifiesto: todas coinciden en número de filas y hash lógico.

Los once nombres con espacios al inicio o al final se conservaron. La comprobación
no recorta nombres, no redondea coordenadas, no cambia el algoritmo de hash y no
reescribe datos ni manifiestos. Que Windows coincida no demuestra todavía la causa
de la diferencia reportada en macOS.

Los [resultados por entorno](../../reports/etapa3/verificacion_estaciones_windows_20261031.json)
contienen conteos, tipos y hashes, sin filas del catálogo. El comparador publica
dos hashes por columna: uno de su representación CSV y otro de sus valores. En
el segundo, los números de punto flotante se representan en hexadecimal para
distinguir una diferencia de valores de una diferencia de formato.

## Cómo repetir la comparación

Usar el mismo commit y los manifiestos confirmados. El programa está en
`scripts/check_station_manifest.py` y exige un nombre nuevo para cada salida.
El entorno del proyecto ya contiene sus dependencias.

En Windows, desde la raíz del repositorio y con el entorno correspondiente:

```powershell
python scripts/check_station_manifest.py --output private_quality/estaciones_windows_proyecto.json
.venv-deepchecks/Scripts/python.exe scripts/check_station_manifest.py --verify-outputs --output private_quality/estaciones_windows_deepchecks.json
```

En macOS, desde la raíz del repositorio:

```bash
python scripts/check_station_manifest.py --output private_quality/estaciones_macos_proyecto.json
.venv-deepchecks/bin/python scripts/check_station_manifest.py --verify-outputs --output private_quality/estaciones_macos_deepchecks.json
```

Si los datos están en otro clon, `--project-root` permite indicar su raíz. La
salida 0 indica coincidencia de todas las comprobaciones solicitadas; la salida 1
indica una diferencia. Una entrada ausente o inválida produce un error de ejecución,
que tampoco cuenta como aprobación. Los JSON pueden compartirse para comparar
`source_sha256`, `expected_stations`, los tipos y los hashes por columna.

La comprobación de 151 archivos revisa identidad, no constituye una nueva ejecución
de las reglas de DeepChecks sobre los datos reales. No se ejecutó la etapa `final`
ni se cambió la política que Diego Martinez mantiene en borrador.

## Pruebas del comparador

Se aprobaron seis pruebas: catálogo coincidente sin alterar archivos, cambio de una
coordenada, salida faltante, fuente modificada aunque sus valores sigan iguales,
orden de filas y espacios, y rechazo de una salida que sobrescriba la entrada.
Antes de agregar este último control también pasaron 38 casos del comparador y de
ingesta. Son ejecuciones que se superponen; no se suman como pruebas distintas.
Bandit no reportó hallazgos en el nuevo script. Los registros completos permanecen
en el directorio privado de calidad.

## Actualización parcial de setuptools

La auditoría del archivo de dependencias propuesto en el PR #35 encontró nueve
entradas de avisos, correspondientes a cinco identificadores distintos, para
`setuptools==65.5.0`. Esta versión también estaba instalada implícitamente en el
entorno de comprobación local: la auditoría anterior del archivo de requisitos no
la incluía porque no aparecía en ese archivo.

Se fija `setuptools==81.0.0` de forma explícita. Se comprobó `pip check` y se
repitieron los controles reales de compatibilidad de DeepChecks: la columna
variable pasa y la columna constante es rechazada. La auditoría de la propuesta
del PR #35, sustituyendo únicamente esa versión, baja a tres entradas y dos
identificadores distintos. Es una reducción parcial, no un cierre de seguridad.

Los avisos restantes son `PYSEC-2026-3447` (exclusiones Unicode al construir paquetes)
y `GHSA-xmj3-9gf7-h52w` (ruta heredada de instalación de paquetes en Windows).
El auditor indica correcciones en 83.0.0 y 84.1.0, respectivamente. Sin embargo,
Setuptools retiró `pkg_resources` desde 82.0.0 y DeepChecks 0.19.1 todavía lo importa.
Una actualización directa requiere resolver primero esa compatibilidad.

El entorno separado se utiliza para validación; no debe usarse para construir o
publicar distribuciones ni instalar paquetes mediante mecanismos heredados. Estas
restricciones acotan el uso, pero no eliminan los avisos ni equivalen a aceptar el
riesgo. El equipo debe resolver o justificar los hallazgos antes del cierre final.
No se alteraron las versiones de MLflow, PyArrow ni los modelos registrados.

El [resumen de auditoría y compatibilidad](../../reports/etapa3/seguridad_deepchecks_20261031.json)
conserva identificadores, versiones, hashes y el alcance de la comprobación.

## Dependencias para continuar

- Diego Martinez: ejecutar el comparador en macOS y contrastar los hashes por
  columna; conciliar la versión de setuptools del PR #35 con esta actualización.
- Diego Hurtado: revisar el PR #35; Stefania y Diego Hurtado confirman los criterios
  de sus preguntas antes de congelar la política.
- Marco: atender la revisión de esta aportación y contrastar los resultados de
  ambos sistemas cuando esté disponible la salida de macOS. El cierre integrado
  espera los PR revisados y la política congelada.

## Referencias

- Python Packaging Authority. (s. f.). [History: Setuptools](https://setuptools.pypa.io/en/latest/history.html).
- Deepchecks. (2024). [Deepchecks 0.19.1](https://pypi.org/project/deepchecks/0.19.1/).
- Python Packaging Authority. (s. f.). [pip-audit](https://pypi.org/project/pip-audit/).
