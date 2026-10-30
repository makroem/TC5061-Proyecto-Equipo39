# Contrato de calidad de la Etapa 3

Propuesta de Marco para revisión del equipo, 28 de octubre de 2026.
Base: `7aa3b639af13c9c5efb7c750a527f3a5cbc3868e` de `main`.
Este documento fija la interfaz de trabajo; no acredita el cierre de la actividad.

## Alcance y responsables

| Responsable | Entrega | Revisión prevista |
|---|---|---|
| Marco | Entorno de calidad, pruebas de ingesta, exclusiones, seguridad y comprobación integrada | Stefania |
| Stefania | Pruebas y criterios de P1, calendario y partición | Diego Martinez |
| Diego Martinez | Motor DeepChecks, política de calidad, P2 y contratos del registro temporal | Diego Hurtado |
| Diego Hurtado | P3, perfiles, interpretación de calidad, organización de evidencias y README final | Marco |

Cada integrante aporta un PR y revisa el de otro integrante en esta entrega.
El autor no aprueba su propio PR. La integración depende de la revisión independiente
y de las reglas de protección de `main`. Un reemplazo de revisor debe acordarse con el equipo.

## Datos y aislamiento

Las fuentes, fechas y semillas siguen en `mibici_equipo39/config.py`.
Se conserva el periodo de octubre de 2025 a septiembre de 2026, semilla 39 y
`chronological_holdout` versión 3: entrenamiento hasta mayo, validación junio-julio
y prueba agosto-septiembre. Los manifiestos confirmados son la autoridad para la reproducción.

Las pruebas de esta rama usan datos sintéticos, `tmp_path` y almacenes temporales.
No descargan CSV reales, no reemplazan manifiestos oficiales y no modifican los modelos
registrados ni el alias `champion`. Los contratos de MLflow existentes utilizan almacenes
locales de prueba. Las pruebas de descarga HTTP existentes solo escuchan en `127.0.0.1`;
los nuevos casos de interrupción sustituyen la conexión por una respuesta simulada.

## Organización de pruebas

PyTest se configura únicamente en `pyproject.toml`; no se crea un segundo `pytest.ini`.
La colección usa `tests/` y rechaza marcadores desconocidos.

- Sin marcador: pruebas sintéticas que no necesitan servicios.
- `integration`: pruebas con un servidor HTTP local, almacén temporal de MLflow o
  procesos de Git. Las dependencias de fixtures `source`, `contract` y `stage2_env`
  se identifican en `tests/conftest.py`; el caso de Git lleva un marcador explícito.
- `data_quality`: reservado para la validación de datos preparados de la Etapa 3.
  Declarar el marcador no significa que esa validación ya esté implementada.

## Interfaz propuesta para DeepChecks

Diego Martinez implementará `mibici_equipo39/validation/data_checks.py` y
`references/etapa3/quality_policy.json`, con revisión de los responsables de P1/P2/P3.
La interfaz propuesta es:

```text
python -m mibici_equipo39.validation.data_checks --question all --stage development
python -m mibici_equipo39.validation.data_checks --question all --stage final
```

Estos comandos quedan pendientes hasta integrar el motor. `development` analiza train y
validation; `final` añade test con reglas y umbrales ya congelados. No se ajusta la política
para hacer que test pase. El resumen debe registrar pregunta, partición, conteos,
versión de datos, split_id, hash de la política, commit, fecha y resultado por comprobación.

| Estado | Significado |
|---|---|
| PASS | Comprobación ejecutada y criterio satisfecho |
| WARN | Hallazgo que requiere interpretación, sin incumplimiento crítico definido |
| FAIL | Incumplimiento de un criterio crítico explícito |
| NOT_EVALUATED | No pudo ejecutarse; se debe registrar la causa |

Salida 0: comprobaciones obligatorias completas sin fallos críticos; salida 1:
fallo crítico de datos; salida 2: error de ejecución, dependencia o entrada ausente.
Una comprobación obligatoria sin evaluar no puede contarse como aprobada.
Los cambios estacionales no son por sí solos prueba de datos defectuosos.

## Entornos y entregables

`requirements.txt` conserva el entorno del proyecto. `requirements-quality.txt` añade
versiones verificadas para pruebas y seguridad. La compatibilidad de DeepChecks se
documenta por separado antes de acordar su uso con Diego Martinez.
Si requiere otro entorno, debe consumir los mismos datos y manifiestos, sin recalcular
particiones ni importar modelos serializados de un entorno incompatible.

Se publican código, configuraciones, resúmenes y capturas revisadas. Los originales de
datos, bases de MLflow, modelos y salidas sin revisar permanecen fuera de Git.
`private_quality/` y `.venv-*/` están excluidos. Los archivos de evidencia deben incluir
su comando, alcance, commit probado y limitaciones; un escaneo sin alertas no garantiza
ausencia total de vulnerabilidades.

## Condiciones para el cierre

1. Integrar los PR técnicos revisados de los cuatro integrantes.
2. Reproducir desde un clon limpio siguiendo el README publicado.
3. Ejecutar pruebas, validación real con DeepChecks y seguridad sobre el mismo código.
4. Resolver o documentar los hallazgos y responsabilidades pendientes.
5. Diego Hurtado consolida el README y las evidencias; el equipo acuerda quién envía el enlace en Canvas.

La revisión preliminar de Marco no sustituye estos pasos finales.
