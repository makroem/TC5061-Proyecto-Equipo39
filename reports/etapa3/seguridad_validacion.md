# Seguridad del módulo de validación: avisos de Bandit

Tarea #51. Implementó y ejecutó Diego Martinez; revisa Marco. Los resultados verificables están en
[bandit_validacion_vigente.json](bandit_validacion_vigente.json). Los reportes de seguridad
anteriores no se modifican.

## Análisis

| | Antes del cambio | Después del cambio |
|---|---|---|
| Commit analizado | `b1ddc47` (main) | `8812e5a` |
| Hallazgos | 3 LOW, confianza alta | 3 LOW, confianza alta |
| Errores de análisis | Ninguno | Ninguno |

Bandit 1.9.4 con Python 3.11.9, en macOS y en un entorno nuevo instalado desde
`requirements-quality.txt` (`pip check` sin problemas). Comando:

```bash
python -m bandit -r mibici_equipo39/validation -f json -o private_quality/bandit_validacion.json
```

Bandit sale con 1 cuando encuentra hallazgos. Eso no es un error de ejecución: los errores de
análisis aparecen en el campo `errors`, que quedó vacío en las dos corridas.

## Qué hace el código

`git_state()` en `mibici_equipo39/validation/data_checks.py` registra en `summary.json` el commit y si
había cambios locales. Ejecuta dos órdenes fijas, `git rev-parse HEAD` y
`git status --porcelain --untracked-files=normal`, desde la raíz del repositorio y sin shell. No recibe
argumentos del usuario ni de los datos.

## Problemas encontrados y corregidos

Probé la función en repositorios temporales, incluido un `git` falso en el PATH para simular un
proceso que no termina:

| Escenario | Antes | Después |
|---|---|---|
| `git status` falla (índice corrupto) | Commit y repositorio limpio | `(None, None)` |
| Archivo nuevo con `status.showUntrackedFiles=no` | Repositorio limpio | Con cambios |
| Git no termina | La corrida se bloquea | `(None, None)` a los 10 s |
| El ejecutable no se puede iniciar (`OSError`) | Error de ejecución, sin resumen | `(None, None)` |
| Sin Git o fuera de un repositorio | `(None, None)` | Sin cambio |

El primer caso es el que señala la tarea: un fallo de `git status` se reportaba como repositorio
limpio. El segundo lo encontré al revisar: una configuración local podía ocultar archivos nuevos. Se
corrige igual que en `modeling/tracking.py`, que ya pasa `--untracked-files=normal`.

**Contrato ante errores.** `git_state()` regresa `(commit, dirty)` solo si las dos órdenes terminan
con código 0 en menos de 10 segundos. En cualquier otro caso regresa `(None, None)`, y en
`summary.json` quedan `commit` y `git_dirty` en `null`, que significa "no comprobado", nunca
"limpio". La salida del motor no cambia, porque Git no es una comprobación de datos. Una corrida con
`commit` nulo no es trazable y no debe usarse como evidencia.

## Hallazgos

### B404: importación de `subprocess` (`data_checks.py:20`)

- **Operación:** el módulo importa `subprocess` solo para `git_state()`. Son las dos únicas llamadas
  a procesos externos del módulo.
- **Riesgo:** que un cambio posterior use `subprocess` con shell o con argumentos externos.
- **Decisión:** se mantiene. Leer `.git` directamente o agregar GitPython reimplementaría Git o
  sumaría una dependencia sin reducir el riesgo.
- **Riesgo residual:** bajo. Cualquier llamada nueva a `subprocess` debe revisarse con este mismo
  criterio.

### B603: llamadas sin shell (`data_checks.py:49` y `:53`)

- **Operación:** `git rev-parse HEAD` y `git status --porcelain --untracked-files=normal`.
- **Riesgo:** ejecutar un programa distinto de Git o inyectar argumentos.
- **Controles comprobados:** lista fija de argumentos, sin `shell=True` y sin entrada del usuario o
  de los datos. El ejecutable se resuelve una vez con `shutil.which`, el directorio es la raíz del
  repositorio, hay un timeout de 10 s, la salida se captura sin imprimirse y se comprueba el código
  de salida de las dos órdenes.
- **Decisión:** se mantiene, sin `nosec` ni exclusiones.
- **Riesgo residual:** `shutil.which` confía en el PATH. Quien controle el PATH puede poner otro
  `git`, como hice en la prueba. Es el mismo supuesto que para `python` o `pip` en ese entorno, y el
  motor se ejecuta en el equipo de un integrante, no en un servicio. Una ruta fija no funcionaría
  igual en Windows y macOS.

## Alcance y pendientes

- Este PR no agrega pruebas: las de `git_state()` son la tarea #52 de Stefania y se ajustan a este
  contrato.
- `modeling/tracking.py` tiene su propio `git_state()`, que lanza un error en vez de regresar
  `None`. No se cambió, porque queda fuera de #51.
- Bandit es un análisis estático. Que queden tres avisos bajos explicados no significa que el
  módulo sea seguro en cualquier entorno.
