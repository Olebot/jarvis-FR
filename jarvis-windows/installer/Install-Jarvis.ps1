<#
.SYNOPSIS
    Installeur Jarvis FR pour Windows 11 — Désinstalle anciens Python sur C:,
    installe Python 3.12 + venv + CUDA torch + XTTS-v2 + Whisper + Ollama
    sur le disque choisi par l'utilisateur.

.DESCRIPTION
    À exécuter depuis PowerShell en mode Administrateur.
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

.NOTES
    Cible : NVIDIA RTX 3070 Laptop, CUDA 13.0, Python 3.12
#>

[CmdletBinding()]
param(
    [string]$TargetDrive = "",
    [switch]$SkipPythonCleanup = $false
)

$ErrorActionPreference = "Stop"
$ProgressPreference   = "Continue"

function Write-Section([string]$Title) {
    Write-Host ""
    Write-Host ("=" * 70) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Assert-Admin {
    $current = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($current)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Veuillez relancer PowerShell en mode Administrateur."
    }
}

function Get-TargetDrive {
    param([string]$Provided)
    if ($Provided) { return $Provided.TrimEnd(':').ToUpper() }

    $drives = Get-PSDrive -PSProvider FileSystem | Where-Object { $_.Free -gt 40GB -and $_.Name -ne 'C' }
    Write-Host "`nVolumes disponibles (au moins 40 Go libres, hors C:) :" -ForegroundColor Yellow
    $drives | Format-Table Name, @{N='Libre (Go)'; E={[math]::Round($_.Free/1GB,1)}}, @{N='Total (Go)'; E={[math]::Round(($_.Used+$_.Free)/1GB,1)}}

    do {
        $letter = Read-Host "Sur quel lecteur installer Jarvis ? (ex. D)"
        $letter = $letter.TrimEnd(':').ToUpper()
    } while (-not (Test-Path "$($letter):\"))
    return $letter
}

function Uninstall-OldPython {
    Write-Section "Désinstallation des anciennes versions de Python sur C:"
    & "$PSScriptRoot\Uninstall-OldPython.ps1"
}

function Install-Python312 {
    param([string]$InstallDir)
    Write-Section "Installation de Python 3.12 dans $InstallDir"

    $pythonExe = Join-Path $InstallDir "python.exe"
    if (Test-Path $pythonExe) {
        Write-Host "Python déjà présent dans $InstallDir — on conserve." -ForegroundColor Green
        return $pythonExe
    }

    $installer = "$env:TEMP\python-3.12.7-amd64.exe"
    Write-Host "Téléchargement Python 3.12.7..."
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe" -OutFile $installer

    Write-Host "Installation silencieuse vers $InstallDir..."
    Start-Process -FilePath $installer -ArgumentList @(
        "/quiet",
        "InstallAllUsers=0",
        "PrependPath=0",
        "Include_test=0",
        "TargetDir=$InstallDir",
        "DefaultAllUsersTargetDir=$InstallDir",
        "DefaultJustForMeTargetDir=$InstallDir",
        "AssociateFiles=0",
        "Shortcuts=0"
    ) -Wait -NoNewWindow

    if (-not (Test-Path $pythonExe)) {
        throw "Échec d'installation Python."
    }
    Write-Host "Python 3.12 installé." -ForegroundColor Green
    return $pythonExe
}

function New-PythonVenv {
    param([string]$PythonExe, [string]$VenvDir)
    Write-Section "Création de l'environnement virtuel : $VenvDir"
    if (Test-Path $VenvDir) {
        Write-Host "venv déjà présent, on saute." -ForegroundColor Green
        return
    }
    & $PythonExe -m venv $VenvDir
    & "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip wheel setuptools
}

function Install-PythonDeps {
    param([string]$VenvDir, [string]$ReqFile)
    Write-Section "Installation des dépendances Python (CUDA 13.0)"

    $pip = "$VenvDir\Scripts\pip.exe"

    Write-Host "torch + torchaudio CUDA 13.0 (~2 Go)..."
    & $pip install --no-cache-dir torch==2.11.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu130

    Write-Host "Reste des dépendances..."
    & $pip install --no-cache-dir -r $ReqFile

    Write-Host "Installation Playwright Chromium..."
    & "$VenvDir\Scripts\python.exe" -m playwright install chromium
}

function Install-Ollama {
    param([string]$OllamaDir)
    Write-Section "Installation d'Ollama dans $OllamaDir"

    if (Test-Path "$OllamaDir\ollama.exe") {
        Write-Host "Ollama déjà présent." -ForegroundColor Green
        return
    }

    $installer = "$env:TEMP\OllamaSetup.exe"
    Write-Host "Téléchargement Ollama..."
    Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $installer

    # Ollama Setup ne supporte pas /D sur tous les builds ; on installe puis on déplace,
    # et on définit OLLAMA_MODELS pour stocker les modèles sur le disque choisi.
    Write-Host "Installation Ollama (silencieuse)..."
    Start-Process -FilePath $installer -ArgumentList "/SILENT" -Wait -NoNewWindow

    [Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $OllamaDir + "\models", "User")
    Write-Host "OLLAMA_MODELS=$OllamaDir\models (les modèles seront stockés ici)" -ForegroundColor Green
}

function Pull-OllamaModel {
    Write-Section "Téléchargement du modèle Ollama"
    $model = Read-Host "Quel modèle ? [llama3.1:8b] (ou mistral:7b, qwen2.5:7b)"
    if (-not $model) { $model = "llama3.1:8b" }
    Write-Host "ollama pull $model ..."
    & ollama pull $model
    return $model
}

function Copy-ProjectFiles {
    param([string]$InstallRoot)
    Write-Section "Copie des fichiers Jarvis vers $InstallRoot"

    $projectRoot = Split-Path -Parent $PSScriptRoot
    Copy-Item -Path "$projectRoot\jarvis"   -Destination $InstallRoot -Recurse -Force
    Copy-Item -Path "$projectRoot\config"   -Destination $InstallRoot -Recurse -Force
    Copy-Item -Path "$projectRoot\voices"   -Destination $InstallRoot -Recurse -Force
    Copy-Item -Path "$projectRoot\README.md" -Destination $InstallRoot -Force

    # config par défaut si absent
    $cfg = Join-Path $InstallRoot "config\config.yaml"
    if (-not (Test-Path $cfg)) {
        Copy-Item "$InstallRoot\config\config.example.yaml" $cfg
    }
    $env = Join-Path $InstallRoot "config\.env"
    if (-not (Test-Path $env)) {
        Copy-Item "$InstallRoot\config\.env.example" $env
    }
}

function New-Launcher {
    param([string]$InstallRoot, [string]$VenvDir, [string]$Model)
    Write-Section "Création des lanceurs"

    $bat = @"
@echo off
setlocal
set JARVIS_HOME=$InstallRoot
set OLLAMA_MODELS=$InstallRoot\ollama\models
cd /d "$InstallRoot"
"$VenvDir\Scripts\python.exe" -m jarvis.main
endlocal
"@
    Set-Content -Path "$InstallRoot\start-jarvis.bat" -Value $bat -Encoding ASCII

    # Raccourci Bureau
    $WshShell = New-Object -ComObject WScript.Shell
    $shortcut = $WshShell.CreateShortcut("$([Environment]::GetFolderPath('Desktop'))\Jarvis.lnk")
    $shortcut.TargetPath = "$InstallRoot\start-jarvis.bat"
    $shortcut.WorkingDirectory = $InstallRoot
    $shortcut.IconLocation = "$InstallRoot\jarvis\ui\jarvis.ico,0"
    $shortcut.Save()

    Write-Host "Raccourci Bureau créé." -ForegroundColor Green
}

# ============================================================
# Main
# ============================================================
Assert-Admin

Write-Section "JARVIS FR — Installation Windows 11 (RTX 3070)"

$drive = Get-TargetDrive -Provided $TargetDrive
$installRoot = "${drive}:\Jarvis"
$pythonDir   = "$installRoot\python312"
$venvDir     = "$installRoot\venv"
$ollamaDir   = "$installRoot\ollama"

Write-Host "`nTout sera installé dans : $installRoot" -ForegroundColor Yellow
$confirm = Read-Host "Continuer ? (O/N)"
if ($confirm -ne "O" -and $confirm -ne "o") { exit }

New-Item -ItemType Directory -Force -Path $installRoot, $ollamaDir | Out-Null

if (-not $SkipPythonCleanup) {
    $cleanup = Read-Host "Désinstaller les Python existants sur C: ? (O/N) [O]"
    if ($cleanup -ne "N" -and $cleanup -ne "n") {
        Uninstall-OldPython
    }
}

$pythonExe = Install-Python312 -InstallDir $pythonDir
New-PythonVenv -PythonExe $pythonExe -VenvDir $venvDir
Install-PythonDeps -VenvDir $venvDir -ReqFile "$PSScriptRoot\requirements.txt"
Install-Ollama -OllamaDir $ollamaDir

Copy-ProjectFiles -InstallRoot $installRoot

# ollama serve démarre tout seul comme service ; on attend qu'il soit prêt
Start-Sleep -Seconds 5
$model = Pull-OllamaModel

New-Launcher -InstallRoot $installRoot -VenvDir $venvDir -Model $model

Write-Section "Installation terminée"
Write-Host "1. Placez votre client_secret.json Google dans : $installRoot\config\client_secret.json" -ForegroundColor Yellow
Write-Host "2. Éditez : $installRoot\config\config.yaml" -ForegroundColor Yellow
Write-Host "3. Double-cliquez sur le raccourci 'Jarvis' du Bureau." -ForegroundColor Green
