<#
Installs the help-skill into Claude's skills folder.

  .\install.ps1            personal install: <config>\skills\help-skill
  .\install.ps1 -Project   project install:  .\.claude\skills\help-skill

<config> is $env:CLAUDE_CONFIG_DIR when set, otherwise $HOME\.claude.
An existing copy is moved to a skills-backup folder first.
#>
param(
    [switch]$Project
)

$ErrorActionPreference = 'Stop'

$source = Join-Path $PSScriptRoot 'skills\help-skill'
if (-not (Test-Path (Join-Path $source 'SKILL.md'))) {
    Write-Error "Cannot find skills\help-skill\SKILL.md next to this script."
}

if ($Project) {
    $base = Join-Path (Get-Location) '.claude'
} elseif ($env:CLAUDE_CONFIG_DIR) {
    $base = $env:CLAUDE_CONFIG_DIR
} else {
    $base = Join-Path $HOME '.claude'
}

$skillsDir = Join-Path $base 'skills'
$target = Join-Path $skillsDir 'help-skill'

if (Test-Path $target) {
    $backupDir = Join-Path $base 'skills-backup'
    New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
    $backup = Join-Path $backupDir ("help-skill-" + (Get-Date -Format 'yyyyMMdd-HHmmss'))
    Move-Item -Path $target -Destination $backup
    Write-Host "Existing copy moved to $backup"
}

New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null
Copy-Item -Path $source -Destination $target -Recurse
Get-ChildItem -Path $target -Recurse -Directory -Filter '__pycache__' |
    Remove-Item -Recurse -Force

Write-Host "Installed help-skill to $target"

$python = Get-Command python, python3, py -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $python) {
    Write-Warning "Python was not found. The skill needs Python 3.9 or newer for its inventory script."
}

Write-Host "Start a new Claude session, then try: /help-skill <your task>"
