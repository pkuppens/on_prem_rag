#Requires -Version 5.1
<#
.SYNOPSIS
    Creates a directory junction from .cursor/skills to the canonical skills tree in a sibling pkuppens/pkuppens clone.

.DESCRIPTION
    Expected layout (same parent folder as this repo):

        <parent>/
          on_prem_rag/     # this repository
          pkuppens/        # clone of https://github.com/pkuppens/pkuppens (contains skills/)

    Run once after clone, or when .cursor/skills is missing. Safe to re-run: replaces only the junction.

.NOTES
    Uses a junction (no admin) so Git does not try to add the whole skills tree. See docs/technical/SKILLS_SETUP.md.
#>

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $repoRoot "..\pkuppens\skills" | Resolve-Path
$cursorDir = Join-Path $repoRoot ".cursor"
$linkPath = Join-Path $cursorDir "skills"

if (-not (Test-Path $target)) {
    Write-Error "Skills target not found: $target. Clone https://github.com/pkuppens/pkuppens next to this repo (see docs/technical/SKILLS_SETUP.md)."
}

if (-not (Test-Path $cursorDir)) {
    New-Item -ItemType Directory -Path $cursorDir | Out-Null
}

if (Test-Path $linkPath) {
    $item = Get-Item $linkPath -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        cmd /c "rmdir `"$linkPath`""
    } else {
        Write-Error ".cursor/skills exists and is not a link. Remove it manually, then re-run."
    }
}

New-Item -ItemType Junction -Path $linkPath -Target $target.Path | Out-Null
Write-Host "Linked .cursor/skills -> $($target.Path)"
