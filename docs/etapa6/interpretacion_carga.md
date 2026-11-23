# Interpretación de carga y recursos

Preparada por Marco el 19 de noviembre de 2026 como respaldo de la tarea #75. No constituye una aportación de otro integrante ni una nueva ejecución de carga.

## Lectura de las gráficas

La gráfica de rendimiento y latencia reúne tres repeticiones para cada perfil de 1, 10 y 30 usuarios. La mediana de solicitudes por segundo aumenta de 2.91 a 21.16 y 23.12, mientras la mediana del p95 pasa de 51 a 460 y 1700 milisegundos. Aumentar la concurrencia de 10 a 30 usuarios aporta poco rendimiento y eleva la espera. Los rangos del p95, 39–59, 370–840 y 1300–2400 ms, muestran variación entre ejecuciones; no son intervalos de confianza.

Cero fallos de solicitud no implica cumplir el objetivo de latencia. Bajo las condiciones evaluadas, el perfil de 10 usuarios concurrentes parece ofrecer una mejor relación entre capacidad de procesamiento y tiempo de respuesta que el de 30 usuarios. Sin embargo, sus tres repeticiones superan el objetivo nominal de 250 ms y la mediana del p95 es de 460 ms; esa comparación favorable no acredita el cumplimiento del objetivo. Aunque el escenario de 30 usuarios incrementa la carga atendida, el aumento obtenido es reducido en comparación con el deterioro observado en la latencia, por lo que podría no representar una configuración conveniente para aplicaciones sensibles al tiempo de respuesta.

La segunda gráfica, de recursos, muestra que la CPU media de la API se aproxima a su cuota al crecer la carga. La memoria máxima se expresa en MiB; las bandas resumen mínimos y máximos de tres repeticiones. Este patrón es compatible con saturación, pero no demuestra una causa aislada: servicios, generador y tareas auxiliares compartieron anfitrión.

Conviene repetir con el equipo dedicado y contrastar una modificación por vez, conservando P1, entradas y protocolo. Los lotes pueden amortizar costo, siempre que su latencia sea admisible. Los [archivos originales del ensayo de Diego Hurtado](../../references/etapa6/mediciones_diego_hurtado/20261122_151708/README.md) ya están integrados mediante #82 y permiten contrastar sus resultados. Esa ejecución cumplió sus objetivos, pero una sola repetición por perfil y las condiciones históricas parcialmente documentadas impiden atribuir la diferencia frente a Marco a una optimización o extrapolar capacidad de producción. La interrupción puntual del muestreo de recursos del perfil de 30 usuarios se conserva y se describe en el [seguimiento](estado.md).

## Evidencia y referencias

- [Rendimiento y latencia](../../references/etapa6/mediciones_marco/rendimiento_latencia.png), desde [performance.csv](../../references/etapa6/mediciones_marco/performance.csv).
- [Recursos](../../references/etapa6/mediciones_marco/recursos.png), desde [resources.csv](../../references/etapa6/mediciones_marco/resources.csv).
- [Aprobación y alcance del contraste](cierre_revision_20261119.md).

Tres fuentes oficiales consultadas el 19 de noviembre de 2026:

1. [Docker Compose](https://docs.docker.com/compose/): definición de servicios, redes y volúmenes en una configuración común.
2. [Locust 2.47.0](https://docs.locust.io/en/stable/): escenarios de usuarios y ejecución de carga; corresponde a la versión fijada en Compose.
3. [AWS Lightsail](https://aws.amazon.com/lightsail/pricing/): se confirmó el plan Linux/Unix con IPv4 de 24 USD/mes, 2 vCPU y 4 GB. La tarifa alimenta una estimación; no mide rendimiento en la nube ni incluye los costos excluidos en el protocolo.
