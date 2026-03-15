[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$TempRoot,
    [switch]$IncludeTempLogs
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

function Get-ConfiguredTempPath {
    if ($TempRoot) {
        return $TempRoot
    }

    if ($env:TEMP_PATH) {
        return $env:TEMP_PATH
    }

    $envFile = Join-Path $RepoRoot ".env"
    if (-not (Test-Path -LiteralPath $envFile)) {
        return $null
    }

    $line = Get-Content -LiteralPath $envFile |
        Where-Object { $_ -match '^TEMP_PATH=' } |
        Select-Object -First 1

    if (-not $line) {
        return $null
    }

    return ($line -replace '^TEMP_PATH=', '').Trim()
}

function Normalize-Path {
    param([string]$Path)

    return [System.IO.Path]::GetFullPath($Path).TrimEnd('\').ToLowerInvariant()
}

function Test-IsProtectedPath {
    param(
        [string]$Path,
        [string[]]$ProtectedRoots
    )

    $normalizedPath = Normalize-Path $Path
    foreach ($root in $ProtectedRoots) {
        if (-not $root) {
            continue
        }

        $normalizedRoot = Normalize-Path $root
        if ($normalizedPath -eq $normalizedRoot -or
            $normalizedPath.StartsWith($normalizedRoot + "\")) {
            return $true
        }
    }

    return $false
}

function Get-ScopedItems {
    param(
        [string]$Root,
        [string[]]$ProtectedRoots
    )

    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
        return @()
    }

    $items = New-Object System.Collections.Generic.List[object]
    $pending = New-Object System.Collections.Generic.Queue[string]
    $pending.Enqueue((Normalize-Path $Root))

    while ($pending.Count -gt 0) {
        $current = $pending.Dequeue()

        foreach ($item in Get-ChildItem -LiteralPath $current -Force -ErrorAction SilentlyContinue) {
            if (Test-IsProtectedPath -Path $item.FullName -ProtectedRoots $ProtectedRoots) {
                continue
            }

            $items.Add($item)
            if ($item.PSIsContainer) {
                $pending.Enqueue($item.FullName)
            }
        }
    }

    return $items
}

function Get-ItemSizeBytes {
    param([System.IO.FileSystemInfo]$Item)

    if (-not $Item) {
        return 0
    }

    if ($Item.PSIsContainer) {
        $size = (Get-ChildItem -LiteralPath $Item.FullName -Recurse -Force -File -ErrorAction SilentlyContinue |
            Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        if ($null -eq $size) {
            return 0
        }
        return $size
    }

    return $Item.Length
}

function Remove-MatchedItems {
    param(
        [string]$Root,
        [string[]]$Patterns,
        [string[]]$ProtectedRoots,
        [ref]$DeletedCount,
        [ref]$DeletedSize
    )

    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
        return
    }

    $candidates = Get-ScopedItems -Root $Root -ProtectedRoots $ProtectedRoots
    $seen = @{}
    $matchedItems = @()

    foreach ($item in $candidates) {
        foreach ($pattern in $Patterns) {
            if ($item.Name -like $pattern) {
                if (-not $seen.ContainsKey($item.FullName)) {
                    $seen[$item.FullName] = $true
                    $matchedItems += $item
                }
                break
            }
        }
    }

    $selectedItems = New-Object System.Collections.Generic.List[object]
    $selectedContainerRoots = New-Object System.Collections.Generic.List[string]

    foreach ($item in ($matchedItems | Sort-Object { $_.FullName.Length })) {
        $normalizedItemPath = Normalize-Path $item.FullName
        $isNestedUnderSelectedContainer = $false

        foreach ($selectedContainerRoot in $selectedContainerRoots) {
            if ($normalizedItemPath.StartsWith($selectedContainerRoot + "\")) {
                $isNestedUnderSelectedContainer = $true
                break
            }
        }

        if ($isNestedUnderSelectedContainer) {
            continue
        }

        $selectedItems.Add($item)
        if ($item.PSIsContainer) {
            $selectedContainerRoots.Add($normalizedItemPath)
        }
    }

    $matchedItems = $selectedItems | Sort-Object { $_.FullName.Length } -Descending

    foreach ($item in $matchedItems) {
        $size = Get-ItemSizeBytes -Item $item
        $sizeMB = [math]::Round($size / 1MB, 2)
        $normalizedRoot = Normalize-Path $Root
        $normalizedItemPath = Normalize-Path $item.FullName
        if ($normalizedItemPath.StartsWith($normalizedRoot + "\")) {
            $relPath = $normalizedItemPath.Substring($normalizedRoot.Length + 1)
        } else {
            $relPath = $normalizedItemPath
        }

        if ($DryRun) {
            Write-Host "  [planned] $relPath ($sizeMB MB)" -ForegroundColor Yellow
            $DeletedCount.Value++
            $DeletedSize.Value += $size
            continue
        }

        try {
            if ($item.PSIsContainer) {
                Remove-Item -LiteralPath $item.FullName -Recurse -Force -ErrorAction Stop
            } else {
                Remove-Item -LiteralPath $item.FullName -Force -ErrorAction Stop
            }

            Write-Host "  [removed] $relPath ($sizeMB MB)" -ForegroundColor Gray
            $DeletedCount.Value++
            $DeletedSize.Value += $size
        } catch {
            Write-Host "  [failed] $relPath - $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}

$ConfiguredTempRoot = Get-ConfiguredTempPath

$RepoPatterns = @(
    "__pycache__", "*.pyc", "*.pyo", "*.egg-info",
    ".pytest_cache", ".coverage", "htmlcov", ".tox", ".nox", ".hypothesis",
    ".tmp", "*.tmp", "*.temp", "*.bak", "*.backup",
    ".specstory", ".claude",
    ".ruff_cache", ".mypy_cache",
    "pytest-tmp", "pytest_temp", "pytest_tmp*", "pytest-cache-files-*"
)

$TempPatterns = @(
    "backtest", "audit", "pytest", "preflight", "artifacts",
    "pdf-inspect", "pdf_work", "repo-archives",
    "pytest_*", "pytest-*", "pas-ablation-smoke*.json",
    ".reports", "cache", "tachibana", "python-shims", "gs*.exe"
)

if ($IncludeTempLogs) {
    $TempPatterns += "logs"
}

$RepoProtectedRoots = @(
    (Join-Path $RepoRoot ".git"),
    (Join-Path $RepoRoot ".venv"),
    (Join-Path $RepoRoot ".vscode"),
    (Join-Path $RepoRoot "docs\reference")
)

$TempProtectedRoots = @()
if ($ConfiguredTempRoot) {
    $TempProtectedRoots += Join-Path $ConfiguredTempRoot "codex-home"
    if (-not $IncludeTempLogs) {
        $TempProtectedRoots += Join-Path $ConfiguredTempRoot "logs"
    }
}

$TotalDeleted = 0
$TotalSize = 0

Write-Host "EmotionQuant temp cleanup tool" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Repo root: $RepoRoot" -ForegroundColor Cyan
if ($ConfiguredTempRoot) {
    Write-Host "Temp root: $ConfiguredTempRoot" -ForegroundColor Cyan
}
Write-Host "Protected roots: .git / .venv / .vscode / docs\\reference / codex-home" -ForegroundColor Cyan
if (-not $IncludeTempLogs) {
    Write-Host "TEMP_PATH/logs is kept by default. Use -IncludeTempLogs to remove it." -ForegroundColor Cyan
}
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN] Preview only. Nothing will be removed." -ForegroundColor Yellow
    Write-Host ""
}

Write-Host "[Scanning...]" -ForegroundColor Green
Write-Host ""

Remove-MatchedItems -Root $RepoRoot -Patterns $RepoPatterns -ProtectedRoots $RepoProtectedRoots -DeletedCount ([ref]$TotalDeleted) -DeletedSize ([ref]$TotalSize)
Remove-MatchedItems -Root $ConfiguredTempRoot -Patterns $TempPatterns -ProtectedRoots $TempProtectedRoots -DeletedCount ([ref]$TotalDeleted) -DeletedSize ([ref]$TotalSize)

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
$TotalSizeMB = [math]::Round($TotalSize / 1MB, 2)

if ($DryRun) {
    Write-Host "Planned removals: $TotalDeleted items, reclaim: $TotalSizeMB MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Tip: rerun without -DryRun to execute cleanup." -ForegroundColor Cyan
} else {
    Write-Host "Removed: $TotalDeleted items, reclaimed: $TotalSizeMB MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "Tip: runtime caches will be recreated under TEMP_PATH as needed." -ForegroundColor Cyan
}
