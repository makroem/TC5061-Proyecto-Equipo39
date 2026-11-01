# Verificación del catálogo y seguimiento del entorno DeepChecks

Marco realizó esta comprobación el 31 de octubre de 2026, después del aviso de
Diego Martinez en el [PR #35](https://github.com/makroem/TC5061-Proyecto-Equipo39/pull/35).
El objetivo fue confirmar el resultado en Windows y comparar los valores con la
evidencia de macOS aportada por Diego Martinez.

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
reescribe datos ni manifiestos. La primera comprobación quedó registrada antes de
recibir la evidencia de macOS; el contraste posterior se presenta a continuación.

Los [resultados por entorno](../../reports/etapa3/verificacion_estaciones_windows_20261031.json)
contienen conteos, tipos y hashes, sin filas del catálogo. El comparador publica
dos hashes por columna: uno de su representación CSV y otro de sus valores. En
el segundo, los números de punto flotante se representan en hexadecimal para
distinguir una diferencia de valores de una diferencia de formato.

## Contraste recibido de macOS y comprobación del redondeo

Diego Martinez publicó la comparación de macOS ARM y un programa que reproduce
dos formas de redondear la conversión decimal a punto flotante en el
[commit 94624fa del PR #35](https://github.com/makroem/TC5061-Proyecto-Equipo39/commit/94624fa7d71a05ca16bd672b7adf4887b8c0e0c0).
Marco ejecutó ese mismo programa, sin modificarlo, en Windows AMD64 con NumPy
2.1.3 y 1.26.4. También ejecutó sus cinco pruebas: todas aprobaron.

En ambos entornos de Windows, la emulación de dos redondeos reproduce los valores
locales y el hash oficial. La emulación de un solo redondeo produce exactamente
el hash del catálogo reportado en macOS:
`6559e1e45604a5156c4673d23ad6632d8084a278c2be4e639d8b6e7deef3abd8`.
Las emulaciones difieren en 15 latitudes, con una diferencia máxima de
`7.105427357601002e-15` grados; no hay diferencias de longitud. La evidencia de
macOS confirma que las otras seis columnas conservan los mismos tipos y hashes
de valores que Windows. Los once nombres con espacios también coinciden.

La diferencia del hash del archivo del manifiesto se reproduce al cambiar
únicamente sus finales de línea entre LF y CRLF. Este hash de bytes es distinto
del hash lógico del catálogo. Se calcularon ambas representaciones en memoria,
sin reescribir el manifiesto.

El [contraste de resultados](../../reports/etapa3/contraste_estaciones_20261031.json)
conserva la procedencia del programa, los hashes y las verificaciones. El resultado
es consistente con una diferencia de redondeo durante la conversión numérica;
no se inspeccionó el binario de pandas ni se demuestra qué instrucción ejecuta
el procesador. La evidencia de macOS corresponde a Diego Martinez; la repetición
de Marco corresponde a Windows.

Con esto queda atendida la comprobación entre equipos, pero permanece una
limitación de portabilidad exacta: el catálogo de macOS no coincide con el
manifiesto oficial y su control debe seguir marcando diferencia. La validación
final se ejecutará en el entorno Windows AMD64 ya contrastado, después de integrar
los cambios revisados y confirmar la política. No se modifican hashes esperados,
coordenadas ni reglas para convertir una diferencia en una aprobación.

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

Estado al 31 de octubre de 2026, después del commit 94624fa del PR #35:

- Diego Martinez ya entregó el contraste de macOS y fijó setuptools 81.0.0 en
  el PR #35. Falta atender la revisión de Diego Hurtado: proteger también la
  construcción de los conjuntos de DeepChecks, registrar un error inesperado
  como `NOT_EVALUATED` con su causa y probar el código de salida del caso crítico.
- Diego Hurtado ya confirmó los criterios de P3. Debe revisar la corrección
  anterior y completar la revisión del PR #35.
- Stefania debe atender los cambios solicitados en el PR #33, confirmar los
  criterios de P1 en el PR #35 y revisar esta aportación en el PR #36.
- Marco ya reprodujo la explicación numérica en sus dos entornos. Debe atender
  la revisión del PR #36 y, cuando estén los PR aprobados y la política congelada,
  comprobar el conjunto integrado y preparar la evidencia final. Los dos avisos
  de seguridad descritos arriba siguen abiertos.

Los PR #35 y #36 incluyen la misma versión de setuptools. Al integrar el segundo,
se deberá resolver el conflicto de líneas contiguas en el archivo de dependencias
conservando las dependencias acordadas. No se ha realizado ninguna integración.

## Referencias

- Python Packaging Authority. (s. f.). [History: Setuptools](https://setuptools.pypa.io/en/latest/history.html).
- Deepchecks. (2024). [Deepchecks 0.19.1](https://pypi.org/project/deepchecks/0.19.1/).
- Python Packaging Authority. (s. f.). [pip-audit](https://pypi.org/project/pip-audit/).
