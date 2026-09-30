# First-use bootstrap launcher for Windows (PowerShell).
# Detects a Python 3 interpreter, then runs the cross-platform bootstrap.
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path

$py = Get-Command py -ErrorAction SilentlyContinue
if ($py) {
    & $py.Source -3 (Join-Path $dir "bootstrap.py") @args
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if ($python) {
    & $python.Source (Join-Path $dir "bootstrap.py") @args
    exit $LASTEXITCODE
}

Write-Error "Python 3.10+ is required. Install it from https://www.python.org/downloads/ and rerun this script."
exit 1
