# ?? Markdown ???????????????????????
param(
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$MarkdownFiles = Get-ChildItem -Path $RepoRoot -Recurse -File -Include *.md -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notmatch 'pytest-cache-files-' }
$LegacyPatterns = @(
    'docs/design-v2/system-baseline.md',
    'docs/design-v2/architecture-master.md',
    'docs/design-v2/data-layer-design.md',
    'docs/design-v2/selector-design.md',
    'docs/design-v2/strategy-design.md',
    'docs/design-v2/broker-design.md',
    'docs/design-v2/backtest-report-design.md',
    'docs/design-v2/mss-algorithm.md',
    'docs/design-v2/irs-algorithm.md',
    'docs/design-v2/pas-algorithm.md',
    'docs/design-v2/down-to-top-integration.md',
    'docs/design-v2/sandbox-review-standard.md',
    'docs/design-v2/volman-ytc-mapping.md',
    'docs/reference/????/god_view_8_perspectives_report_v0.01.md'
)

$Issues = New-Object System.Collections.Generic.List[object]

foreach ($File in $MarkdownFiles) {
    $Lines = Get-Content -LiteralPath $File.FullName
    $InCodeFence = $false

    for ($Index = 0; $Index -lt $Lines.Length; $Index++) {
        $Line = $Lines[$Index]
        $Trimmed = $Line.Trim()

        if ($Trimmed.StartsWith('```')) {
            $InCodeFence = -not $InCodeFence
            continue
        }

        if ($InCodeFence) {
            continue
        }

        foreach ($Pattern in $LegacyPatterns) {
            if ($Line.Contains($Pattern)) {
                $Issues.Add([pscustomobject]@{
                    Type   = 'stale_path'
                    File   = $File.FullName.Substring($RepoRoot.Length + 1)
                    Line   = $Index + 1
                    Detail = $Pattern
                })
            }
        }

        $Matches = [regex]::Matches($Line, '\[[^\]]+\]\(([^)]+)\)')
        foreach ($Match in $Matches) {
            $Target = $Match.Groups[1].Value.Trim()
            if (-not $Target -or
                $Target.StartsWith('http') -or
                $Target.StartsWith('https') -or
                $Target.StartsWith('mailto:') -or
                $Target.StartsWith('#')) {
                continue
            }

            $TargetPath = $Target.Split('#')[0]
            if (-not $TargetPath) {
                continue
            }

            $Candidate = if ([System.IO.Path]::IsPathRooted($TargetPath)) {
                $TargetPath
            } else {
                Join-Path $File.DirectoryName $TargetPath
            }

            $Resolved = [System.IO.Path]::GetFullPath($Candidate)
            if (-not (Test-Path -LiteralPath $Resolved)) {
                $Issues.Add([pscustomobject]@{
                    Type   = 'broken_link'
                    File   = $File.FullName.Substring($RepoRoot.Length + 1)
                    Line   = $Index + 1
                    Detail = $TargetPath
                })
            }
        }
    }
}

if ($Issues.Count -eq 0) {
    if (-not $Quiet) {
        Write-Host 'No documentation link/path issues found.' -ForegroundColor Green
    }
    exit 0
}

$Issues |
    Sort-Object File, Line, Type |
    Format-Table -AutoSize |
    Out-String -Width 220 |
    Write-Output

exit 1


