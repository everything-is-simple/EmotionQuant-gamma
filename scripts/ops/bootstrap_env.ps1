[CmdletBinding()]
param(
    [switch]$IncludeFileOps,
    [switch]$RunSmoke
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$venvPath = Join-Path $repoRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"
$repoDriveRoot = [System.IO.Path]::GetPathRoot($repoRoot)
$dataRoot = Join-Path $repoDriveRoot "EmotionQuant_data"
$tempRoot = Join-Path $repoDriveRoot "EmotionQuant-temp"
$envExample = Join-Path $repoRoot ".env.example"
$envFile = Join-Path $repoRoot ".env"

Write-Host "==> repo root: $repoRoot"
Write-Host "==> target venv: $venvPath"

if (-not (Test-Path $dataRoot)) {
    New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
}
if (-not (Test-Path $tempRoot)) {
    New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
}

if (-not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    $envContent = Get-Content $envFile -Raw
    $envContent = $envContent -replace '(?m)^DATA_PATH=$', "DATA_PATH=$dataRoot"
    $envContent = $envContent -replace '(?m)^TEMP_PATH=$', "TEMP_PATH=$tempRoot"
    $envContent = $envContent -replace '(?m)^RAW_DB_PATH=$', "RAW_DB_PATH=$(Join-Path $dataRoot 'duckdb\emotionquant.duckdb')"
    Set-Content -Path $envFile -Value $envContent -Encoding utf8
    Write-Host "==> created .env from .env.example"
}

if (-not (Test-Path $venvPython)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3.10 -m venv $venvPath
    }
    elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python -m venv $venvPath
    }
    else {
        throw "Python launcher not found. Install Python 3.10 first."
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment bootstrap failed: $venvPython not found."
}

Push-Location $repoRoot
try {
    & $venvPython -m pip install --upgrade pip setuptools wheel

    $editableTarget = ".[dev]"
    if ($IncludeFileOps) {
        $editableTarget = ".[dev,fileops]"
    }
    & $venvPython -m pip install -e $editableTarget

    & $venvPython -c "import duckdb,pandas,pyarrow,pytest; print('runtime-import-ok')"
    & $venvPython main.py --help | Out-Null

    if ($RunSmoke) {
        & $venvPython -m pytest -m smoke -q
    }

    Write-Host "==> bootstrap complete"
    Write-Host "   activate: .\.venv\Scripts\Activate.ps1"
    Write-Host "   smoke:    python -m pytest -m smoke -q"
}
finally {
    Pop-Location
}
