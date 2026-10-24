# Validación de la infraestructura

Fecha: 22 de octubre de 2026. Responsable: Marco.

Se ejecutó la suite completa con Python 3.11.9, MLflow 2.22.0 y scikit-learn 1.6.1:
**46 pruebas aprobadas**, 28 advertencias, 93.07 segundos. Se usó un directorio temporal
corto en Windows. Las advertencias corresponden a bibliotecas y a sugerencias de anotación
de tipos; no se actualizaron las dependencias de la entrega anterior.

```powershell
python -m pytest tests -q --tb=short --basetemp=<directorio_corto_de_pruebas>
```

El directorio de pruebas debe ser exclusivo y descartable: pytest puede vaciarlo al iniciar.

El contrato comprueba transporte de artefactos, firma y ejemplo, carga desde otro proceso,
un PythonModel de dos salidas, rechazo de campos personales, rechazo de claves sensibles,
rechazo de manifiestos incompatibles y jerarquía padre búsqueda candidato. Se mantienen las
pruebas anteriores de datos, objetivos, partición, aislamiento y modelos.

Se contrastaron los seis identificadores y todas sus métricas del resumen histórico con
SQLite. Se guardó una copia consistente de la base y 53 archivos de artefactos fuera de Git.
El servidor oficial respondió en localhost y mostró el experimento existente en su interfaz.

`git diff --check` no reportó errores de formato. Se comprobaron reglas de exclusión para
mlflow.db, su journal, mlruns, mlartifacts, .env y resultados privados.

Alcance: se verificó la infraestructura y la compatibilidad anterior. No se han ejecutado
los nueve candidatos nuevos ni registrado ganadores de la segunda entrega. Esas comprobaciones
requieren el controlador y las adaptaciones de los tres responsables, después de revisión.
