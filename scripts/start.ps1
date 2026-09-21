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

    $pythonCandidates = @(
        Get-Command python.exe -CommandType Application -All -ErrorAction SilentlyContinue |
            Where-Object { $_.Path -and $_.Path -notmatch '\\WindowsApps\\' } |
            ForEach-Object { $_.Path } |
            Select-Object -Unique
    )
    $PythonPath = $null
    foreach ($candidate in $pythonCandidates) {
        try {
            $version = @(& $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)[-1]
            if ($LASTEXITCODE -eq 0 -and $version -eq '3.12') {
                $PythonPath = $candidate
                break
            }
        } catch {
            # Try the next discovered application; never render the error text.
        }
    }
    if (-not $PythonPath) {
        Write-StartupDiagnostic 'PYTHON_312_UNAVAILABLE'
        exit 1
    }
    Write-StartupDiagnostic 'PYTHON_RESOLVED' 'version=3.12'
    Write-StartupDiagnostic 'UVICORN_LAUNCHED' "port=$Port"
    try {
        & $PythonPath -m uvicorn backend.app:app --host 127.0.0.1 --port $Port
        $exitCode = $LASTEXITCODE
        Write-StartupDiagnostic 'UVICORN_EXITED' "exit_code=$exitCode"
        exit $exitCode
    } catch {
        $exceptionType = $_.Exception.GetType().Name
        if ($exceptionType -notmatch '^[A-Za-z][A-Za-z0-9_]{0,63}$') { $exceptionType = 'UNKNOWN_EXCEPTION' }
        Write-StartupDiagnostic 'LAUNCH_EXCEPTION' "reason=PYTHON_INVOCATION_FAILED type=$exceptionType"
        exit 1
    }
} catch {
    $exceptionType = $_.Exception.GetType().Name
    if ($exceptionType -notmatch '^[A-Za-z][A-Za-z0-9_]{0,63}$') { $exceptionType = 'UNKNOWN_EXCEPTION' }
    Write-StartupDiagnostic 'LAUNCH_EXCEPTION' "reason=STARTUP_INITIALIZATION_FAILED type=$exceptionType"
    exit 1
}
