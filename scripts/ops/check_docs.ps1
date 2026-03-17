# Docs gate entrypoint.
# Only fans out to authority/status/links checks and returns one combined status.
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$Scripts = @(
    'check_doc_authority.ps1',
    'check_doc_status.ps1',
    'check_doc_links.ps1'
)

$Failed = $false

foreach ($ScriptName in $Scripts) {
    $ScriptPath = Join-Path $PSScriptRoot $ScriptName
    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        Write-Output "Missing script: $ScriptName"
        $Failed = $true
        continue
    }

    if (-not $Quiet) {
        Write-Host "==> $ScriptName" -ForegroundColor Cyan
    }

    if ($Quiet) {
        & $ScriptPath -Quiet
    } else {
        & $ScriptPath
    }

    if ($LASTEXITCODE -ne 0) {
        $Failed = $true
    }
}

if ($Failed) {
    if (-not $Quiet) {
        Write-Host 'Docs gate failed.' -ForegroundColor Red
    }
    exit 1
}

if (-not $Quiet) {
    Write-Host 'Docs gate passed.' -ForegroundColor Green
}

exit 0
