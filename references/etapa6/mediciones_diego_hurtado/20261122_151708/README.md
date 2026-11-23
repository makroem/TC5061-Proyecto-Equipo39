# Evidencia del ensayo independiente - Etapa 6

## 1\. Identificacion

* Responsable: Diego Hurtado
* Proyecto: TC5061-Proyecto-Equipo39
* Tipo: Ensayo original recuperado
* Referencia: PR #72, tarea #74
* Fecha del ensayo: 18 de noviembre de 2026
* Inicio registrado: 21:16:29, UTC-06:00
* Fecha de preparacion: 22 de noviembre de 2026
* Commit ejecutado: a9d8424ceb5090c7a4cc5b0aaeb9fc27e067db60
* Cambios locales durante el ensayo: no registrados

## 2\. Modelo y entorno

* Modelo: mibici-equipo39-p1-demanda
* Version del modelo: 1
* SHA-256 del paquete P1:
dedce1eb08bda971a42fba311224c88e56f75cd2789dbb391e9445951931bd80
* Sistema operativo: Windows; version historica no registrada
* Procesador del equipo: modelo no registrado
* RAM fisica del equipo: no registrada
* Docker Engine: 29.8.0
* CPU disponibles para Docker: 12
* Memoria disponible para Docker: 16268275712 bytes
* Docker Compose: version historica no registrada
* Locust: version historica no verificada
* Generador de carga: comparte el anfitrion
* Otras tareas concurrentes: no registradas

## 3\. Protocolo

* Perfiles: 1, 10 y 30 usuarios
* Repeticiones: 1 por perfil
* Duracion configurada: 90 segundos por perfil
* Calentamiento: 30 segundos
* Spawn rate: 1, 2 y 5 usuarios/s, respectivamente
* Pausas entre tareas: 0.1 a 0.5 segundos
* Pesos de tareas: 4 individuales por 1 de lote
* Cargas: prediccion individual y lote de 10
* Cambios de configuracion durante la prueba: no registrados
* Muestreo de recursos: intervalo objetivo de 2 segundos

## 4\. Resultados originales

|Usuarios|Solicitudes|Fallos|Predicciones utiles|p95 individual|p95 lote 10|
|-|-:|-:|-:|-:|-:|
|1|292|0|787|10 ms|10 ms|
|10|2812|0|7816|22 ms|21 ms|
|30|7466|0|21524|190 ms|180 ms|

Totales:

* Solicitudes: 10570
* Fallos: 0
* Predicciones utiles: 30127

Los tres perfiles cumplieron los limites de p95 y tasa de fallos establecidos para este ensayo.

## 5\. Evidencia incluida

La carpeta originales/ contiene los 21 archivos
recuperados de revision\_diego\_pr72.

Incluye:

* protocol.json y runs.json
* Reportes HTML de Locust
* Resumenes JSON y estadisticas CSV
* Muestras de recursos JSONL
* Registros y archivos de calentamiento

El inventario\_sha256.csv registra las huellas de los
21 archivos. Las copias fueron comparadas con sus
originales mediante SHA-256.

## 6\. Limitaciones

* Se ejecuto una repeticion por perfil, segun protocol.json.
* No se realizaron repeticiones r2 y r3.
* No se dispone de todos los detalles historicos del equipo.
* Las condiciones del anfitrion no estuvieron completamente
controladas ni documentadas.
* El generador compartio recursos con los servicios.
* Los resultados son exploratorios y no acreditan
capacidad de produccion.
* Las diferencias frente a Marco requieren comparaciones
bajo condiciones equivalentes.
* No se modificaron ni sustituyeron las mediciones de Marco.
* tracking\_check.json permanece fuera de este paquete.

## 7\. Trazabilidad

Esta evidencia corresponde al ensayo independiente
declarado durante la revision del PR #72.

La recuperacion y publicacion de archivos corresponde
a la tarea #74.

No se realizaron nuevas pruebas para preparar
este paquete.

