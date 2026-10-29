param(
    [Parameter(Mandatory = $true)][string]$StorePath,
    [string]$PythonExecutable = 'python',
    [ValidateRange(1024, 65535)][int]$Port = 5000
)

$ErrorActionPreference = 'Stop'
$store = (Resolve-Path -LiteralPath $StorePath).Path
if (-not (Test-Path -LiteralPath (Join-Path $store 'mlflow.db') -PathType Leaf)) {
    throw 'La carpeta no contiene mlflow.db. Indica el almacén existente; no se creará una base vacía.'
}
$expectedMlflow = (Get-Content (Join-Path $PSScriptRoot '../requirements.txt') | Where-Object { $_ -match '^mlflow==' }) -replace '^mlflow==', ''
$env:MLFLOW_DISABLE_AGENT_HINT = '1'
$versions = & $PythonExecutable -c 'import sys,mlflow; print(sys.version.split()[0], mlflow.__version__)'
if ($LASTEXITCODE -ne 0 -or $versions -ne "3.11.9 $expectedMlflow") {
    throw "Se requiere Python 3.11.9 y MLflow $expectedMlflow, según requirements.txt."
}
# Impide que un servidor nuevo cambie una base antigua al iniciarse.
$schemaCheck = @'
import sqlite3, sys
from pathlib import Path
from mlflow.store.db.utils import _get_latest_schema_revision
with sqlite3.connect(Path(sys.argv[1]).as_uri() + '?mode=ro', uri=True) as db:
    current = db.execute('SELECT version_num FROM alembic_version').fetchone()[0]
if current != _get_latest_schema_revision():
    raise SystemExit('El esquema no corresponde a esta version. Preparar y validar una copia antes de iniciar el servidor.')
'@
& $PythonExecutable -c $schemaCheck (Join-Path $store 'mlflow.db')
if ($LASTEXITCODE -ne 0) { throw 'La base requiere el procedimiento de migración documentado.' }
Write-Output 'Entorno validado'
Push-Location -LiteralPath $store
try {
    & $PythonExecutable -m mlflow server --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlartifacts --serve-artifacts --host 127.0.0.1 --port $Port --workers 1
    if ($LASTEXITCODE -ne 0) { throw 'El servidor de MLflow terminó con error.' }
}
finally { Pop-Location }
