# SPDX-FileCopyrightText: 2026 Toon Verstraelen <Toon.Verstraelen@UGent.be>
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# Install Typst and Tectonic in the Windows test VM of StepUp Core,
# so that the examples of tests/test_examples.py that need them run there.
# See ../stepup-core/tools/winvm/README.md for the VM.
# Run this once from the root of the VM checkout,
# and again to install other versions:
#
#     powershell -ExecutionPolicy Bypass -File tools\winvm-tools.ps1
#
# Both programs are put on the PATH of the machine,
# and FONTCONFIG_FILE is set for the machine, which requires an administrator.
# The tests skip the examples when other versions than 0.15.x and 0.17.x are found.

param(
    [string]$TypstVersion = '0.15.1',
    [string]$TectonicVersion = '0.17.0'
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$downloads = Join-Path $env:TEMP 'winvm-tools'
New-Item -ItemType Directory -Force -Path $downloads | Out-Null

function Invoke-Checked {
    # Run a console program and throw if it fails.
    # Progress output on stderr must not count as an error, hence the local preference.
    param([string]$FilePath, [string[]]$ArgumentList)
    $ErrorActionPreference = 'Continue'
    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) { throw "$FilePath exited with code $LASTEXITCODE" }
}

function Get-File {
    param([string]$Url, [string]$Name)
    $path = Join-Path $downloads $Name
    Write-Host "Downloading $Url"
    Invoke-Checked 'curl.exe' @(
        '--fail', '--location', '--retry', '5', '--retry-all-errors', '--output', $path, $Url
    )
    return $path
}

function Add-MachinePath {
    # The current session gets the directory too, for the warm-up and the checks below.
    param([string]$Directory)
    $path = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    if (($path -split ';') -notcontains $Directory) {
        [Environment]::SetEnvironmentVariable('Path', "$path;$Directory", 'Machine')
    }
    if (($env:Path -split ';') -notcontains $Directory) {
        $env:Path = "$env:Path;$Directory"
    }
}

function Install-Program {
    # Copy the program from a ZIP file to its own directory,
    # wherever the archive keeps it, because Typst puts it in a subdirectory and Tectonic does not.
    param([string]$Url, [string]$Program)
    $zip = Get-File $Url "$Program.zip"
    $unpacked = Join-Path $downloads $Program
    if (Test-Path $unpacked) { Remove-Item -Recurse -Force $unpacked }
    Expand-Archive -Path $zip -DestinationPath $unpacked
    $exe = Get-ChildItem -Path $unpacked -Recurse -Filter "$Program.exe" | Select-Object -First 1
    if (-not $exe) { throw "$Program.exe not found in $Url" }
    $directory = Join-Path $env:ProgramFiles $Program
    New-Item -ItemType Directory -Force -Path $directory | Out-Null
    Copy-Item -Path $exe.FullName -Destination $directory -Force
    Add-MachinePath $directory
    Invoke-Checked $Program @('--version')
}

Write-Host "==> Installing Typst $TypstVersion"
Install-Program -Program 'typst' -Url (
    "https://github.com/typst/typst/releases/download/v$TypstVersion/" +
    'typst-x86_64-pc-windows-msvc.zip'
)

Write-Host "==> Installing Tectonic $TectonicVersion"
Install-Program -Program 'tectonic' -Url (
    "https://github.com/tectonic-typesetting/tectonic/releases/download/" +
    "tectonic%40$TectonicVersion/tectonic-$TectonicVersion-x86_64-pc-windows-msvc.zip"
)

Write-Host '==> Configuring fontconfig for Tectonic'
# The reason is explained under "Tests on Windows" in docs/development.md.
# The configuration is copied, because the VM checkout is replaced by every sync.
$fontsConf = Join-Path $env:ProgramFiles 'tectonic\fonts.conf'
Copy-Item -Path (Join-Path $PSScriptRoot 'fonts.conf') -Destination $fontsConf -Force
[Environment]::SetEnvironmentVariable('FONTCONFIG_FILE', $fontsConf, 'Machine')
$env:FONTCONFIG_FILE = $fontsConf

Write-Host '==> Warming up the cache of Tectonic'
# On first use, Tectonic downloads its bundle and builds a LaTeX format,
# which takes longer than an example may run.
# This document needs the same files of the bundle as the examples.
$warmup = Join-Path $downloads 'tectonic-warmup'
New-Item -ItemType Directory -Force -Path $warmup | Out-Null
$github = Join-Path (Split-Path -Parent $PSScriptRoot) '.github'
Copy-Item -Path (Join-Path $github 'warmup.tex'), (Join-Path $github 'warmup.bib') `
    -Destination $warmup -Force
Invoke-Checked 'tectonic' @('-c', 'minimal', (Join-Path $warmup 'warmup.tex'))

Write-Host '==> Typst and Tectonic are installed'
