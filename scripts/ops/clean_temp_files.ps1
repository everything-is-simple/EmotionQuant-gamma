# 清理仓库内缓存与 TEMP_PATH 运行时产物。
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$TempRoot
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

    $line = Get-Content $envFile | Where-Object { $_ -match '^TEMP_PATH=' } | Select-Object -First 1
    if (-not $line) {
        return $null
    }
    return ($line -replace '^TEMP_PATH=', '').Trim()
}

function Remove-MatchedItems {
    param(
        [string]$Root,
        [string[]]$Patterns,
        [ref]$DeletedCount,
        [ref]$DeletedSize
    )

    if (-not $Root -or -not (Test-Path -LiteralPath $Root)) {
        return
    }

    foreach ($Pattern in $Patterns) {
        $Items = Get-ChildItem -Path $Root -Recurse -Force -ErrorAction SilentlyContinue |
            Where-Object {
                $_.Name -like $Pattern -and
                $_.FullName -notlike "*\.git\*" -and
                $_.FullName -notlike "*\docs\reference\*"
            }

        foreach ($Item in $Items) {
            $Size = 0
            if ($Item.PSIsContainer) {
                $Size = (Get-ChildItem -Path $Item.FullName -Recurse -Force -ErrorAction SilentlyContinue |
                    Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
            } else {
                $Size = $Item.Length
            }
            if ($null -eq $Size) {
                $Size = 0
            }

            $SizeMB = [math]::Round($Size / 1MB, 2)
            $RelPath = $Item.FullName.Replace($Root + "\", "")

            if ($DryRun) {
                Write-Host "  [将删除] $RelPath ($SizeMB MB)" -ForegroundColor Yellow
                $DeletedCount.Value++
                $DeletedSize.Value += $Size
                continue
            }

            try {
                if ($Item.PSIsContainer) {
                    Remove-Item -Path $Item.FullName -Recurse -Force -ErrorAction Stop
                } else {
                    Remove-Item -Path $Item.FullName -Force -ErrorAction Stop
                }
                Write-Host "  [已删除] $RelPath ($SizeMB MB)" -ForegroundColor Gray
                $DeletedCount.Value++
                $DeletedSize.Value += $Size
            } catch {
                Write-Host "  [失败] $RelPath - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

$ConfiguredTempRoot = Get-ConfiguredTempPath

Write-Host "EmotionQuant 临时文件清理工具" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "仓库根目录: $RepoRoot" -ForegroundColor Cyan
if ($ConfiguredTempRoot) {
    Write-Host "临时目录: $ConfiguredTempRoot" -ForegroundColor Cyan
}
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN 模式] 仅显示将要删除的内容，不实际删除" -ForegroundColor Yellow
    Write-Host ""
}

$RepoPatterns = @(
    "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.so", "*.egg-info",
    ".pytest_cache", ".coverage", "htmlcov", ".tox", ".nox", ".hypothesis",
    ".vscode", ".idea", "*.swp", "*.swo",
    ".tmp", "*.tmp", "*.temp", "*.bak", "*.backup",
    ".specstory", ".claude",
    ".ruff_cache", ".mypy_cache", "pytest-tmp", "pytest_temp", "pytest_tmp*", "pytest-cache-files-*",
    "*.log", "logs"
)
$TempPatterns = @(
    "backtest", "audit", "pytest", "preflight", "artifacts",
    "pdf-inspect", "repo-archives", "pytest_*", "pytest-*", "pas-ablation-smoke*.json"
)

$TotalDeleted = 0
$TotalSize = 0

Write-Host "[开始扫描...]" -ForegroundColor Green
Write-Host ""

Remove-MatchedItems -Root $RepoRoot -Patterns $RepoPatterns -DeletedCount ([ref]$TotalDeleted) -DeletedSize ([ref]$TotalSize)
Remove-MatchedItems -Root $ConfiguredTempRoot -Patterns $TempPatterns -DeletedCount ([ref]$TotalDeleted) -DeletedSize ([ref]$TotalSize)

Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
$TotalSizeMB = [math]::Round($TotalSize / 1MB, 2)

if ($DryRun) {
    Write-Host "预计删除: $TotalDeleted 项，释放空间: $TotalSizeMB MB" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "提示: 使用不带 -DryRun 参数执行实际删除" -ForegroundColor Cyan
} else {
    Write-Host "已删除: $TotalDeleted 项，释放空间: $TotalSizeMB MB" -ForegroundColor Green
    Write-Host ""
    Write-Host "提示: 运行时缓存会在后续开发中按 TEMP_PATH 重新生成" -ForegroundColor Cyan
}
