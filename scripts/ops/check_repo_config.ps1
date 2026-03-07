# ???????????????????hooks ????????????
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$RequiredFiles = @(
    'pyproject.toml',
    '.env.example',
    '.githooks/pre-commit',
    'scripts/ops/preflight.ps1',
    'scripts/ops/check_docs.ps1',
    'scripts/ops/check_path_discipline.ps1'
)
$RequiredPyprojectSections = @(
    '[tool.pytest.ini_options]',
    '[tool.ruff]',
    '[tool.mypy]'
)
$Errors = New-Object System.Collections.Generic.List[string]

foreach ($relativePath in $RequiredFiles) {
    $fullPath = Join-Path $RepoRoot $relativePath
    if (-not (Test-Path -LiteralPath $fullPath)) {
        $Errors.Add("Missing required file: $relativePath")
    }
}

$pyprojectPath = Join-Path $RepoRoot 'pyproject.toml'
if (Test-Path -LiteralPath $pyprojectPath) {
    $pyproject = Get-Content -Raw -Encoding UTF8 $pyprojectPath
    foreach ($section in $RequiredPyprojectSections) {
        if ($pyproject -notmatch [regex]::Escape($section)) {
            $Errors.Add("Missing pyproject section: $section")
        }
    }
}

try {
    $hooksPath = git config --get core.hooksPath 2>$null
    if ([string]::IsNullOrWhiteSpace($hooksPath)) {
        $Errors.Add('Git core.hooksPath is not configured.')
    } elseif ($hooksPath.Trim() -ne '.githooks') {
        $Errors.Add("Git core.hooksPath must be '.githooks' but is '$($hooksPath.Trim())'.")
    }
} catch {
    $Errors.Add('Failed to read git core.hooksPath.')
}

if ($Errors.Count -gt 0) {
    foreach ($message in $Errors) {
        Write-Output $message
    }
    exit 1
}

if (-not $Quiet) {
    Write-Host 'Repository config check passed.' -ForegroundColor Green
}

exit 0

