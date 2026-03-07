# Check document status/seal-date semantics for design-v2 and steering headers.
param(
    [switch]$Quiet
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot '..\..')
$Targets = @(
    (Join-Path $RepoRoot 'docs/design-v2'),
    (Join-Path $RepoRoot 'docs/steering')
)
$ExpectedSealByStatus = @{
    'Active' = '不适用（Active SoT）'
    'Draft' = '不适用（Draft）'
}
$Issues = New-Object System.Collections.Generic.List[string]

function Get-MetadataValue {
    param(
        [string[]]$Lines,
        [string]$FieldName
    )

    $prefix = "**$FieldName**:"
    $line = $Lines | Where-Object { $_.TrimStart().StartsWith($prefix) } | Select-Object -First 1
    if (-not $line) {
        return $null
    }

    $raw = $line.Substring($line.IndexOf(':') + 1).Trim()
    if ($raw.StartsWith('`')) {
        $closing = $raw.IndexOf('`', 1)
        if ($closing -gt 1) {
            return $raw.Substring(1, $closing - 1)
        }
    }

    return ($raw -split '\s+')[0]
}

foreach ($target in $Targets) {
    Get-ChildItem -Path $target -Recurse -Filter *.md | ForEach-Object {
        $lines = Get-Content -Encoding UTF8 $_.FullName | Select-Object -First 20
        $status = Get-MetadataValue -Lines $lines -FieldName '状态'
        $sealDate = Get-MetadataValue -Lines $lines -FieldName '封版日期'
        $relativePath = Resolve-Path -Relative $_.FullName

        if (-not $status) {
            $Issues.Add("${relativePath}: missing **状态** metadata.")
            return
        }

        if ($status -notin @('Frozen', 'Active', 'Draft')) {
            $Issues.Add("${relativePath}: invalid 状态 '$status'.")
            return
        }

        if (-not $sealDate) {
            $Issues.Add("${relativePath}: missing **封版日期** metadata.")
            return
        }

        switch ($status) {
            'Frozen' {
                if ($sealDate -notmatch '^\d{4}-\d{2}-\d{2}$') {
                    $Issues.Add("${relativePath}: Frozen documents must use a concrete 封版日期, got '$sealDate'.")
                }
            }
            'Active' {
                if ($sealDate -ne $ExpectedSealByStatus['Active']) {
                    $Issues.Add("${relativePath}: Active documents must use '$($ExpectedSealByStatus['Active'])', got '$sealDate'.")
                }
            }
            'Draft' {
                if ($sealDate -ne $ExpectedSealByStatus['Draft']) {
                    $Issues.Add("${relativePath}: Draft documents must use '$($ExpectedSealByStatus['Draft'])', got '$sealDate'.")
                }
            }
        }
    }
}

if ($Issues.Count -gt 0) {
    foreach ($issue in $Issues) {
        Write-Output $issue
    }
    exit 1
}

if (-not $Quiet) {
    Write-Host 'Document status semantics check passed.' -ForegroundColor Green
}

exit 0