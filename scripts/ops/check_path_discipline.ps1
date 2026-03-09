# 检查 src/ 与 scripts/ 中是否出现仓库根目录临时路径硬编码。
[CmdletBinding()]
param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Targets = @("src", "scripts")
$IgnoreRelativePaths = @(
    "scripts/ops/check_path_discipline.ps1"
)
$Rules = @(
    @{
        Name = "absolute-repo-temp"
        Pattern = '(?i)EmotionQuant-gamma[\\/](?:\.tmp|pytest-tmp|pytest_temp|\.pytest_cache|\.mypy_cache|\.ruff_cache|artifacts)(?:[\\/]|$)'
        Message = "Hardcoded repo-root temp path"
    },
    @{
        Name = "python-relative-temp"
        Pattern = '(?i)\bPath\s*\(\s*["''](?:\.tmp|pytest-tmp|pytest_temp|\.pytest_cache|\.mypy_cache|\.ruff_cache|artifacts)(?:[\\/][^"'']*)?["'']\s*\)'
        Message = "Relative temp path via Path(...)"
    },
    @{
        Name = "python-repo-root-temp"
        Pattern = '(?i)\brepo_root\s*/\s*["''](?:\.tmp|pytest-tmp|pytest_temp|\.pytest_cache|\.mypy_cache|\.ruff_cache|artifacts)(?:[\\/][^"'']*)?["'']'
        Message = "repo_root temp path composition"
    },
    @{
        Name = "powershell-repo-root-temp"
        Pattern = '(?i)\bJoin-Path\s+\$RepoRoot\s+["''](?:\.tmp|pytest-tmp|pytest_temp|\.pytest_cache|\.mypy_cache|\.ruff_cache|artifacts)(?:[\\/][^"'']*)?["'']'
        Message = "Join-Path RepoRoot temp path"
    }
)
$Violations = New-Object System.Collections.Generic.List[string]

foreach ($target in $Targets) {
    $targetPath = Join-Path $RepoRoot $target
    if (-not (Test-Path -LiteralPath $targetPath)) {
        continue
    }

    $files = Get-ChildItem -Path $targetPath -Recurse -File -Include *.py, *.ps1
    foreach ($file in $files) {
        $relativePath = $file.FullName.Replace($RepoRoot.Path + "\", "").Replace("\", "/")
        if ($relativePath -in $IgnoreRelativePaths) {
            continue
        }

        $lines = Get-Content -Encoding UTF8 $file.FullName
        for ($index = 0; $index -lt $lines.Count; $index++) {
            $line = $lines[$index]
            foreach ($rule in $Rules) {
                if ($line -match $rule.Pattern) {
                    $message = "{0}:{1}: {2}: {3}" -f $relativePath, ($index + 1), $rule.Message, $line.Trim()
                    $Violations.Add($message)
                }
            }
        }
    }
}

if ($Violations.Count -gt 0) {
    foreach ($violation in $Violations) {
        Write-Output $violation
    }
    exit 1
}

if (-not $Quiet) {
    Write-Host "Path discipline check passed." -ForegroundColor Green
}

exit 0
