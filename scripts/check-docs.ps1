<#
.SYNOPSIS
    Check a project's documentation set: required files, required sections,
    relative links, ADR numbering, and leftover template placeholders.

.DESCRIPTION
    Section requirements come from references/checks.json so this script stays
    pure ASCII. Windows PowerShell 5.1 reads a BOM-less .ps1 as ANSI, so any
    non-ASCII literal here would be corrupted at parse time. Keep it ASCII.

.PARAMETER Root
    Project root. Defaults to the current directory.

.PARAMETER Config
    Path to checks.json. Defaults to ../references/checks.json of this script.

.PARAMETER Strict
    Treat leftover template placeholders as failures instead of warnings.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-docs.ps1 -Root .
#>
[CmdletBinding()]
param(
    [string] $Root = '.',
    [string] $Config,
    [switch] $Strict
)

$ErrorActionPreference = 'Stop'

if (-not $Config) { $Config = Join-Path $PSScriptRoot '..\references\checks.json' }
$rootPath = (Resolve-Path -LiteralPath $Root).Path
$configPath = (Resolve-Path -LiteralPath $Config).Path
$settings = Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json

$script:failures = 0
$script:warnings = 0

function Add-Finding {
    param([string] $Level, [string] $Message)
    if ($Level -eq 'FAIL') {
        Write-Host "FAIL  $Message" -ForegroundColor Red
        $script:failures++
    } elseif ($Level -eq 'WARN') {
        Write-Host "WARN  $Message" -ForegroundColor Yellow
        $script:warnings++
    } else {
        Write-Host "ok    $Message" -ForegroundColor Green
    }
}

function Read-Doc {
    param([string] $Path)
    return [System.IO.File]::ReadAllText($Path, [System.Text.Encoding]::UTF8)
}

function Get-ProjectDocs {
    param([string] $RootPath)
    $skip = '(?i)[\\/](\.git|node_modules|\.dsh|\.agents|\.venv|dist|build)[\\/]'
    return @(Get-ChildItem -LiteralPath $RootPath -Recurse -Filter '*.md' -File |
        Where-Object { $_.FullName -notmatch $skip })
}

$marker = '<!-- fill'
if ($settings.placeholderMarker) { $marker = [string]$settings.placeholderMarker }

# --- 1. required files and sections -----------------------------------------

$requiredCount = 0
foreach ($item in $settings.requiredFiles.PSObject.Properties) {
    $requiredCount++
    $relative = $item.Name.Replace('/', '\')
    $path = Join-Path $rootPath $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Add-Finding 'FAIL' "missing file: $($item.Name)"
        continue
    }
    $text = Read-Doc $path
    $missing = @()
    foreach ($section in @($item.Value)) {
        if ($text.IndexOf([string]$section, [System.StringComparison]::Ordinal) -lt 0) {
            $missing += [string]$section
        }
    }
    if ($missing.Count -eq 0) {
        Add-Finding 'ok' "sections: $($item.Name)"
    } else {
        Add-Finding 'FAIL' ("missing section in {0}: {1}" -f $item.Name, ($missing -join ', '))
    }
}
if ($requiredCount -eq 0) { Add-Finding 'WARN' 'checks.json lists no required files' }

# --- 2. relative links ------------------------------------------------------

# The skill's own material must never be scanned as project documentation: when
# this repository is itself the skill package, references/ holds the templates.
$materialRoot = (Join-Path (Split-Path -Parent $PSScriptRoot) 'references').TrimEnd('\') + '\'
$docs = @(Get-ProjectDocs $rootPath | Where-Object { -not $_.FullName.StartsWith($materialRoot, [System.StringComparison]::OrdinalIgnoreCase) })
$linkPattern = '\[[^\]]*\]\(\s*(?<target>[^)\s]+)'
$broken = 0
foreach ($doc in $docs) {
    $text = Read-Doc $doc.FullName
    foreach ($match in [regex]::Matches($text, $linkPattern)) {
        $target = $match.Groups['target'].Value
        if ($target -match '^[a-zA-Z][a-zA-Z0-9+.-]*:') { continue }
        if ($target.StartsWith('#') -or $target.StartsWith('/')) { continue }
        $clean = ($target -split '#')[0]
        if ([string]::IsNullOrWhiteSpace($clean)) { continue }
        $clean = $clean.Trim('<', '>').Replace('/', '\')
        $candidate = Join-Path $doc.DirectoryName $clean
        if (-not (Test-Path -LiteralPath $candidate)) {
            $broken++
            $shown = $doc.FullName.Substring($rootPath.Length).TrimStart('\')
            Add-Finding 'WARN' ("broken link in {0}: {1}" -f $shown, $target)
        }
    }
}
if ($broken -eq 0) { Add-Finding 'ok' 'relative links resolve' }

# --- 3. ADR numbering -------------------------------------------------------

$adrDir = Join-Path $rootPath 'docs\adr'
if (Test-Path -LiteralPath $adrDir -PathType Container) {
    $seen = @{}
    foreach ($file in Get-ChildItem -LiteralPath $adrDir -Filter '*.md' -File | Sort-Object Name) {
        if ($file.Name -notmatch '^(\d{3})-') {
            Add-Finding 'WARN' "adr without number: $($file.Name)"
            continue
        }
        $number = [int]$Matches[1]
        if ($seen.ContainsKey($number)) {
            Add-Finding 'FAIL' ("duplicate adr number {0}: {1} and {2}" -f $number, $seen[$number], $file.Name)
        } else {
            $seen[$number] = $file.Name
        }
    }
    if ($seen.Count -gt 0) {
        $highest = ($seen.Keys | Measure-Object -Maximum).Maximum
        if ($highest -ne $seen.Count) {
            Add-Finding 'WARN' ("adr numbering has gaps: {0} file(s), highest number {1}" -f $seen.Count, $highest)
        } else {
            Add-Finding 'ok' ("adr numbering contiguous: {0} file(s)" -f $seen.Count)
        }
    }
}

# --- 4. leftover template placeholders --------------------------------------

$placeholderFiles = 0
foreach ($doc in $docs) {
    $body = [regex]::Replace((Read-Doc $doc.FullName), '`[^`\r\n]*`', '')
    $count = ([regex]::Matches($body, [regex]::Escape($marker))).Count
    if ($count -le 0) { continue }
    $placeholderFiles++
    $shown = $doc.FullName.Substring($rootPath.Length).TrimStart('\')
    if ($Strict) {
        Add-Finding 'FAIL' ("unfilled placeholder x{0} in {1}" -f $count, $shown)
    } else {
        Add-Finding 'WARN' ("unfilled placeholder x{0} in {1}" -f $count, $shown)
    }
}
if ($placeholderFiles -eq 0) { Add-Finding 'ok' 'no unfilled placeholders' }

# --- summary ----------------------------------------------------------------

Write-Host ''
Write-Host ("{0} failure(s), {1} warning(s) under {2}" -f $script:failures, $script:warnings, $rootPath)
if ($script:failures -gt 0) { exit 1 }
exit 0
