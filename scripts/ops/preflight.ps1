# Unified preflight entrypoint.
# Runs docs/config/path/lint/test checks by profile before commit or push.
param(
    [switch]$Quiet,
    [switch]$DocsOnly,
    [string]$Profile = "default",
    [string[]]$Checks = @()
)

$ErrorActionPreference = "Stop"
$AllowedProfiles = @("default", "hook", "docs", "full")
if ($Profile -notin $AllowedProfiles) {
    Write-Output ("Unknown profile: " + $Profile)
    exit 1
}

$DocsScript = Join-Path $PSScriptRoot "check_docs.ps1"
$ConfigScript = Join-Path $PSScriptRoot "check_repo_config.ps1"
$PathScript = Join-Path $PSScriptRoot "check_path_discipline.ps1"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

function Get-ConfiguredTempPath {
    if ($env:TEMP_PATH) {
        return $env:TEMP_PATH
    }

    $envFile = Join-Path $RepoRoot ".env"
    if (-not (Test-Path -LiteralPath $envFile)) {
        return $null
    }

    $line = Get-Content $envFile | Where-Object { $_ -match '^TEMP_PATH=' } | Select-Object -First 1
    if (-not $line) {
        return $null
    }

    return ($line -replace '^TEMP_PATH=', '').Trim()
}

function Get-RepoTempRoot {
    $configured = Get-ConfiguredTempPath
    if ($configured) {
        return [System.IO.Path]::GetFullPath($configured)
    }

    return Join-Path ([System.IO.Path]::GetTempPath()) "EmotionQuant"
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    if (-not $Quiet) {
        Write-Host ("==> " + $Name) -ForegroundColor Cyan
    }

    & $Action

    if ($LASTEXITCODE -ne 0) {
        throw ($Name + " failed.")
    }
}

function Test-PythonModule {
    param([string]$Module)

    & python -m $Module --version *> $null
    return $LASTEXITCODE -eq 0
}

function Assert-PythonModule {
    param([string]$Module)

    if (-not (Test-PythonModule -Module $Module)) {
        throw ("Missing python module: " + $Module + ". Install dev dependencies first, e.g. `pip install -e .[dev]`.")
    }
}

function Resolve-SelectedChecks {
    if ($DocsOnly) {
        return @("docs")
    }

    if ($Checks.Count -gt 0) {
        return $Checks
    }

    switch ($Profile) {
        "docs" { return @("docs") }
        "full" { return @("docs", "config", "paths", "lint", "test") }
        "hook" { return @("docs", "config", "paths") }
        default { return @("docs", "config", "paths") }
    }
}

$SelectedChecks = Resolve-SelectedChecks
$KnownChecks = @("docs", "config", "paths", "lint", "test")
$UnknownChecks = $SelectedChecks | Where-Object { $_ -notin $KnownChecks }
if ($UnknownChecks) {
    Write-Output ("Unknown checks: " + ($UnknownChecks -join ", "))
    exit 1
}

foreach ($requiredScript in @($DocsScript, $ConfigScript, $PathScript)) {
    if (-not (Test-Path -LiteralPath $requiredScript)) {
        Write-Output ("Missing script: " + (Split-Path -Leaf $requiredScript))
        exit 1
    }
}

try {
    foreach ($check in $SelectedChecks) {
        switch ($check) {
            "docs" {
                Invoke-Step -Name "docs gate" -Action {
                    if ($Quiet) {
                        & $DocsScript -Quiet
                    } else {
                        & $DocsScript
                    }
                }
            }
            "config" {
                Invoke-Step -Name "repo config" -Action {
                    if ($Quiet) {
                        & $ConfigScript -Quiet
                    } else {
                        & $ConfigScript
                    }
                }
            }
            "paths" {
                Invoke-Step -Name "path discipline" -Action {
                    if ($Quiet) {
                        & $PathScript -Quiet
                    } else {
                        & $PathScript
                    }
                }
            }
            "lint" {
                Assert-PythonModule -Module "ruff"
                Assert-PythonModule -Module "mypy"
                $tempRoot = Join-Path (Get-RepoTempRoot) "preflight"
                $ruffCache = Join-Path $tempRoot "ruff-cache"
                $mypyCache = Join-Path $tempRoot "mypy-cache"
                New-Item -ItemType Directory -Force -Path $ruffCache | Out-Null
                New-Item -ItemType Directory -Force -Path $mypyCache | Out-Null

                Invoke-Step -Name "ruff" -Action {
                    & python -m ruff check . --cache-dir $ruffCache
                }
                Invoke-Step -Name "mypy" -Action {
                    $env:MYPY_CACHE_DIR = $mypyCache
                    & python -m mypy src
                }
            }
            "test" {
                Assert-PythonModule -Module "pytest"

                Invoke-Step -Name "pytest" -Action {
                    $runId = [System.Guid]::NewGuid().ToString("N")
                    $baseTemp = Join-Path (Join-Path (Get-RepoTempRoot) "pytest") ("eq-pytest-" + $runId)
                    $sessionTemp = Join-Path $baseTemp "temp"
                    New-Item -ItemType Directory -Force -Path $sessionTemp | Out-Null
                    $env:TMP = (Resolve-Path $sessionTemp).Path
                    $env:TEMP = $env:TMP
                    $env:TMPDIR = $env:TMP
                    & python -m pytest -q --basetemp $baseTemp -p no:cacheprovider
                }
            }
        }
    }
} catch {
    Write-Output $_.Exception.Message
    if (-not $Quiet) {
        Write-Host "Preflight failed." -ForegroundColor Red
    }
    exit 1
}

if (-not $Quiet) {
    Write-Host "Preflight passed." -ForegroundColor Green
}

exit 0
