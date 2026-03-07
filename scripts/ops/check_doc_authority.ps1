# ?? README / AGENTS / docs/*/README ?????? baseline?development-status ? docs/spec??????????
param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$Targets = New-Object System.Collections.Generic.List[string]
$Targets.Add((Join-Path $RepoRoot 'README.md'))
$AgentsPath = Join-Path $RepoRoot 'AGENTS.md'
if (Test-Path -LiteralPath $AgentsPath) {
    $Targets.Add($AgentsPath)
}
Get-ChildItem -Path (Join-Path $RepoRoot 'docs') -Recurse -File -Filter README.md | ForEach-Object {
    $Targets.Add($_.FullName)
}

$Requirements = @(
    [pscustomobject]@{
        Name = 'baseline'
        Canonical = 'docs/design-v2/01-system/system-baseline.md'
        Regex = '(?i)(docs/design-v2/01-system/system-baseline\.md|(?:\.\./)+design-v2/01-system/system-baseline\.md|01-system/system-baseline\.md|system-baseline\.md)'
    },
    [pscustomobject]@{
        Name = 'development_status'
        Canonical = 'docs/spec/common/records/development-status.md'
        Regex = '(?i)(docs/spec/common/records/development-status\.md|(?:\.\./)+spec/common/records/development-status\.md|common/records/development-status\.md|development-status\.md)'
    },
    [pscustomobject]@{
        Name = 'spec_root'
        Canonical = 'docs/spec/'
        Regex = '(?i)(docs/spec/|(?:\.\./)+spec/|common/README\.md|spec/<version>)'
    }
)

$Issues = New-Object System.Collections.Generic.List[object]

foreach ($Target in $Targets) {
    if (-not (Test-Path -LiteralPath $Target)) {
        continue
    }

    $Relative = $Target.Substring($RepoRoot.Length + 1) -replace '\\', '/'
    $Content = (Get-Content -LiteralPath $Target -Raw) -replace '\\', '/'

    foreach ($Requirement in $Requirements) {
        if ($Content -notmatch $Requirement.Regex) {
            $Issues.Add([pscustomobject]@{
                File = $Relative
                Missing = $Requirement.Name
                Expected = $Requirement.Canonical
            })
        }
    }
}

if ($Issues.Count -eq 0) {
    if (-not $Quiet) {
        Write-Host 'All authority-entry references are present.' -ForegroundColor Green
    }
    exit 0
}

$Issues |
    Sort-Object File, Missing |
    Format-Table -AutoSize |
    Out-String -Width 220 |
    Write-Output

exit 1

