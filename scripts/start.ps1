param([int]$Port = 8000)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$StartupLog = Join-Path $RepositoryRoot 'logs\startup.log'

function Write-StartupDiagnostic([string]$Code, [string]$Detail = '') {
    $timestamp = (Get-Date).ToUniversalTime().ToString('o')
    $line = if ($Detail) { "$timestamp | $Code | $Detail" } else { "$timestamp | $Code" }
    try {
        New-Item -ItemType Directory -Path (Split-Path -Parent $StartupLog) -Force | Out-Null
        Add-Content -LiteralPath $StartupLog -Value $line -Encoding utf8
        $recent = @(Get-Content -LiteralPath $StartupLog -Tail 40)
        Set-Content -LiteralPath $StartupLog -Value $recent -Encoding utf8
    } catch {
        # Logging is diagnostic-only; it must not prevent the loopback server starting.
    }
}

try {
    if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot 'backend\app.py') -PathType Leaf)) {
        Write-StartupDiagnostic 'REPOSITORY_ROOT_UNAVAILABLE'
        exit 1
    }
    Set-Location -LiteralPath $RepositoryRoot
    Write-StartupDiagnostic 'REPOSITORY_ROOT_READY'

    $python = Get-Command python -CommandType Application -ErrorAction SilentlyContinue
    if (-not $python) {
        Write-StartupDiagnostic 'PYTHON_UNAVAILABLE'
        exit 1
    }
    Write-StartupDiagnostic 'PYTHON_RESOLVED'
    Write-StartupDiagnostic 'UVICORN_LAUNCHED' "port=$Port"
    & $python.Path -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
    $exitCode = $LASTEXITCODE
    Write-StartupDiagnostic 'UVICORN_EXITED' "exit_code=$exitCode"
    exit $exitCode
} catch {
    Write-StartupDiagnostic 'LAUNCH_EXCEPTION'
    exit 1
}
