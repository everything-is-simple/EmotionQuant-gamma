param(
    [string]$DiagramDir = "blueprint/99-diagrams",
    [double]$Scale = 2.0
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$diagramPath = Join-Path $repoRoot $DiagramDir
$configPath = Join-Path $diagramPath "mermaid-config.json"

if (-not (Test-Path $diagramPath)) {
    throw "Diagram directory not found: $diagramPath"
}

if (-not (Test-Path $configPath)) {
    throw "Mermaid config not found: $configPath"
}

$sources = Get-ChildItem -Path $diagramPath -Filter "*.mmd" | Sort-Object Name

if (-not $sources) {
    throw "No Mermaid source files found in: $diagramPath"
}

foreach ($source in $sources) {
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($source.Name)
    $svgPath = Join-Path $diagramPath "$baseName.svg"
    $pngPath = Join-Path $diagramPath "$baseName.png"

    Write-Host "Rendering $($source.Name) -> $([System.IO.Path]::GetFileName($svgPath))"
    npx @mermaid-js/mermaid-cli `
        -i $source.FullName `
        -o $svgPath `
        -c $configPath `
        -b white `
        -s $Scale

    Write-Host "Rendering $($source.Name) -> $([System.IO.Path]::GetFileName($pngPath))"
    npx @mermaid-js/mermaid-cli `
        -i $source.FullName `
        -o $pngPath `
        -c $configPath `
        -b white `
        -s $Scale
}

Write-Host "Done. Rendered $($sources.Count) diagrams in $diagramPath"
