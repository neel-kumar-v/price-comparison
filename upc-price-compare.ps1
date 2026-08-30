#!/usr/bin/env pwsh
# Legacy wrapper — prefer: python compare.py discover|compare
# See WORKFLOW.md and price_compare/ for deterministic retailer steps.

param(
    [Parameter(Position = 0)]
    [ValidateSet("discover", "compare")]
    [string]$Stage = "discover",
    [string]$Query = "hask argan oil conditioner",
    [string]$Title,
    [string]$Size,
    [string]$Upc,
    [string]$Url
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$compare = Join-Path $root "compare.py"

if ($Stage -eq "discover") {
    python $compare discover $Query
    exit $LASTEXITCODE
}

if (-not $Title -or -not $Size) {
    Write-Error "compare stage requires -Title and -Size"
    exit 1
}

$args = @("compare", "--title", $Title, "--size", $Size)
if ($Upc) { $args += @("--upc", $Upc) }
if ($Url) { $args += @("--url", $Url) }
python $compare @args
