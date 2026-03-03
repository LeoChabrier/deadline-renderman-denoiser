<#
.SYNOPSIS
    Copies the custom folder and its contents to a Deadline repository.

.DESCRIPTION
    Recursively copies all files from the local "custom" folder into the
    specified Deadline repository path, preserving the directory structure.
    Warns before overwriting any file that already exists at the destination.

.PARAMETER RootRepositoryPath
    The root path of the target Deadline repository (e.g. \\server\DeadlineRepository).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, HelpMessage = "Path to the Deadline repository root.")]
    [ValidateNotNullOrEmpty()]
    [string]$RootRepositoryPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Resolve paths --------------------------------------------------------

$ScriptDir  = Split-Path -Parent $PSScriptRoot          # repo root
$SourceDir  = Join-Path $ScriptDir "custom"

if (-not (Test-Path $SourceDir)) {
    Write-Error "Source folder not found: $SourceDir"
    exit 1
}

$DestDir = Join-Path $RootRepositoryPath "custom"

# --- Copy with overwrite warnings ----------------------------------------

$Files = Get-ChildItem -Path $SourceDir -Recurse -File

$CopiedCount   = 0
$OverwriteCount = 0
$ErrorCount     = 0

foreach ($File in $Files) {
    $RelativePath = $File.FullName.Substring($SourceDir.Length)
    $DestFile     = Join-Path $DestDir $RelativePath
    $DestFolder   = Split-Path -Parent $DestFile

    # Ensure the target directory exists
    if (-not (Test-Path $DestFolder)) {
        New-Item -ItemType Directory -Path $DestFolder -Force | Out-Null
    }

    # Warn if the file already exists
    if (Test-Path $DestFile) {
        $OverwriteCount++
        Write-Warning "File already exists and will be overwritten: $DestFile"
    }

    try {
        Copy-Item -Path $File.FullName -Destination $DestFile -Force
        Write-Host "  Copied: $RelativePath" -ForegroundColor Green
        $CopiedCount++
    }
    catch {
        Write-Error "Failed to copy '$($File.FullName)': $_"
        $ErrorCount++
    }
}

# --- Summary --------------------------------------------------------------

Write-Host ""
Write-Host "--- Summary ---" -ForegroundColor Cyan
Write-Host "  Files copied     : $CopiedCount"
Write-Host "  Files overwritten : $OverwriteCount"
Write-Host "  Errors            : $ErrorCount"

if ($ErrorCount -gt 0) {
    Write-Warning "Some files could not be copied. Review the errors above."
    exit 1
}

Write-Host "Done." -ForegroundColor Green
