# 清理临时文件和缓存目录
# 用途：清理开发过程中产生的临时文件，保持仓库整洁

param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"
$RepoRoot = "G:/EmotionQuant-gamma"

Write-Host "EmotionQuant 临时文件清理工具" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

if ($DryRun) {
    Write-Host "[DRY RUN 模式] 仅显示将要删除的内容，不实际删除" -ForegroundColor Yellow
    Write-Host ""
}

# 定义要清理的目录和文件模式
$PythonCache = @("__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.so", "*.egg-info")
$TestCache = @(".pytest_cache", ".coverage", "htmlcov", ".tox", ".nox", ".hypothesis")
$IDEConfig = @(".vscode", ".idea", "*.swp", "*.swo")
$TempFiles = @(".tmp", "*.tmp", "*.temp", "*.bak", "*.backup")
$AgentTrace = @(".specstory", ".claude")
$RuntimeArtifacts = @("artifacts", ".reports")
$LogFiles = @("*.log", "logs")

$AllPatterns = $PythonCache + $TestCache + $IDEConfig + $TempFiles + $AgentTrace + $RuntimeArtifacts + $LogFiles

$TotalDeleted = 0
$TotalSize = 0

Write-Host "[开始扫描...]" -ForegroundColor Green
Write-Host ""

foreach ($Pattern in $AllPatterns) {
    $Items = Get-ChildItem -Path $RepoRoot -Recurse -Force -ErrorAction SilentlyContinue | 
             Where-Object { 
                 $_.Name -like $Pattern -and 
                 $_.FullName -notlike "*\.git\*" -and
                 $_.FullName -notlike "*\docs\reference\*"
             }
    
    foreach ($Item in $Items) {
        # 计算大小
        $Size = 0
        if ($Item.PSIsContainer) {
            $Size = (Get-ChildItem -Path $Item.FullName -Recurse -Force -ErrorAction SilentlyContinue | 
                     Measure-Object -Property Length -Sum -ErrorAction SilentlyContinue).Sum
        } else {
            $Size = $Item.Length
        }
        
        if ($null -eq $Size) { $Size = 0 }
        
        $SizeMB = [math]::Round($Size / 1MB, 2)
        $RelPath = $Item.FullName.Replace($RepoRoot + "\", "")
        
        if ($DryRun) {
            Write-Host "  [将删除] $RelPath ($SizeMB MB)" -ForegroundColor Yellow
            $TotalDeleted++
            $TotalSize += $Size
        } else {
            try {
                if ($Item.PSIsContainer) {
                    Remove-Item -Path $Item.FullName -Recurse -Force -ErrorAction Stop
                } else {
                    Remove-Item -Path $Item.FullName -Force -ErrorAction Stop
                }
                Write-Host "  [已删除] $RelPath ($SizeMB MB)" -ForegroundColor Gray
                $TotalDeleted++
                $TotalSize += $Size
            } catch {
                Write-Host "  [失败] $RelPath - $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# 总结
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
    Write-Host "提示: 这些文件会在开发过程中自动重新生成" -ForegroundColor Cyan
}
