# Windows first-use launcher. No global Python/pip or profile edits are required.
$ErrorActionPreference = "Stop"
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$bootstrapArgs = @($args)
foreach ($candidate in @('py', 'python3', 'python')) {
    $python = Get-Command $candidate -CommandType Application -ErrorAction SilentlyContinue
    if (-not $python) { continue }
    # Skip Windows Store aliases, which can open an installer instead of Python.
    if ($python.Source -like '*\Microsoft\WindowsApps\*') { continue }
    $prefix = @()
    if ($candidate -eq 'py') { $prefix = @('-3') }
    & $python.Source @prefix -c 'import sys; raise SystemExit(sys.version_info < (3,10))' 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        & $python.Source @prefix (Join-Path $dir 'bootstrap.py') @bootstrapArgs
        exit $LASTEXITCODE
    }
}
if ($bootstrapArgs -contains '--check') {
    Write-Output '{"ready":false,"missing":["Python 3.10+"],"retry":"Run setup.ps1 without --check to prepare private Python"}'
    exit 1
}
$architecture = $env:PROCESSOR_ARCHITEW6432
if (-not $architecture) { $architecture = $env:PROCESSOR_ARCHITECTURE }
switch ($architecture.ToLowerInvariant()) {
    'amd64' { $key = 'windows-x86_64' }
    'arm64' { $key = 'windows-aarch64' }
    default { throw "No private Python runtime for Windows/$architecture" }
}
$base = $env:LOCALAPPDATA
if (-not $base) { $base = Join-Path $env:USERPROFILE 'AppData\Local' }
$runtime = Join-Path $base 'skill-bank\video-runtime'
if ($env:SKILL_BANK_PYTHON_HOME) { $runtime = $env:SKILL_BANK_PYTHON_HOME }
$tools = Join-Path $runtime 'python-tools'
New-Item -ItemType Directory -Force -Path $tools | Out-Null
$uv = Join-Path $tools 'uv.exe'
$uvReady = $false
if (Test-Path -LiteralPath $uv -PathType Leaf) {
    & $uv --version 2>$null | Out-Null
    $uvReady = $LASTEXITCODE -eq 0
}
if (-not $uvReady) {
    $existing = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue
    if ($existing) {
        & $existing.Source --version 2>$null | Out-Null
        if ($LASTEXITCODE -eq 0) { $uv = $existing.Source; $uvReady = $true }
    }
}
if (-not $uvReady) {
    $pins = Get-Content -LiteralPath (Join-Path $dir 'uv_wheels.json') -Raw | ConvertFrom-Json
    $spec = $pins.platforms.$key
    if (-not $spec) { throw "No prebuilt Python manager for $key" }
    $scratch = Join-Path $tools ('uv-launcher-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $scratch | Out-Null
    $wheel = $null
    try {
        [Console]::Error.WriteLine('Preparing verified private Python manager from PyPI')
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $archive = Join-Path $scratch 'uv.whl'
        Invoke-WebRequest -UseBasicParsing -Uri $spec.url -OutFile $archive -TimeoutSec 180
        if ((Get-Item -LiteralPath $archive).Length -ne $spec.size -or
            (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $spec.sha256) {
            throw 'Private Python manager failed pinned size/SHA-256 verification'
        }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        $wheel = [IO.Compression.ZipFile]::OpenRead($archive)
        $member = $wheel.GetEntry("uv-$($pins.version).data/scripts/uv.exe")
        if (-not $member -or $member.Length -le 0 -or $member.Length -gt 150000000) {
            throw 'Invalid private Python manager binary'
        }
        $staged = Join-Path $scratch 'uv.exe'
        [IO.Compression.ZipFileExtensions]::ExtractToFile($member, $staged)
        $versionText = & $staged --version
        if ($LASTEXITCODE -ne 0 -or -not $versionText.StartsWith("uv $($pins.version)")) {
            throw 'Private Python manager did not verify'
        }
        foreach ($license in @('LICENSE-APACHE', 'LICENSE-MIT')) {
            $entry = $wheel.GetEntry("uv-$($pins.version).dist-info/licenses/$license")
            if (-not $entry -or $entry.Length -gt 100000) { throw 'Invalid Python manager license' }
            $destination = Join-Path $tools "uv-$license"
            [IO.Compression.ZipFileExtensions]::ExtractToFile($entry, $destination, $true)
        }
        Move-Item -LiteralPath $staged -Destination $uv -Force
    } finally {
        if ($wheel) { $wheel.Dispose() }
        Remove-Item -LiteralPath $scratch -Recurse -Force -ErrorAction SilentlyContinue
    }
}
$env:UV_PYTHON_INSTALL_DIR = Join-Path $runtime 'python'
$env:UV_CACHE_DIR = Join-Path $runtime 'uv-cache'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONDONTWRITEBYTECODE = '1'
& $uv run --no-project --no-build --python 3.12 python (Join-Path $dir 'bootstrap.py') @bootstrapArgs
exit $LASTEXITCODE
