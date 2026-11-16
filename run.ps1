param(
    [int]$Port = 8000,
    [switch]$NoReload
)

$ErrorActionPreference = 'Stop'
$pythonPath = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) {
    throw 'Create the environment first: python -m venv .venv'
}

Push-Location -LiteralPath $PSScriptRoot
try {
    $serverArgs = @('-B', '-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', "$Port")
    if (-not $NoReload) { $serverArgs += '--reload' }
    & $pythonPath @serverArgs
    $serverExitCode = $LASTEXITCODE
} finally {
    Pop-Location
}
exit $serverExitCode
