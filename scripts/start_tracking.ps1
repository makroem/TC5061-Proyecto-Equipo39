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
$versions = & $PythonExecutable -c 'import sys,mlflow; print(sys.version.split()[0], mlflow.__version__)'
if ($LASTEXITCODE -ne 0 -or $versions -ne '3.11.9 2.22.0') {
    throw 'Se requiere Python 3.11.9 y MLflow 2.22.0.'
}
Write-Output 'Entorno validado'
Push-Location -LiteralPath $store
try {
    & $PythonExecutable -m mlflow server --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlartifacts --serve-artifacts --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw 'El servidor de MLflow terminó con error.' }
}
finally { Pop-Location }
