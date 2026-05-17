<#
.SYNOPSIS
    Désinstalle proprement Jarvis FR (Python local, venv, modèles, Ollama).
#>

param([string]$InstallRoot = "")

if (-not $InstallRoot) {
    $InstallRoot = Read-Host "Chemin d'installation Jarvis (ex. D:\Jarvis)"
}

if (-not (Test-Path $InstallRoot)) {
    Write-Host "Dossier introuvable : $InstallRoot" -ForegroundColor Red
    exit 1
}

$ok = Read-Host "Confirmer la suppression de $InstallRoot ? (O/N)"
if ($ok -ne "O" -and $ok -ne "o") { exit }

# Stop Ollama
Get-Process ollama -ErrorAction SilentlyContinue | Stop-Process -Force

Remove-Item -Recurse -Force "$InstallRoot"
Remove-Item -Force "$([Environment]::GetFolderPath('Desktop'))\Jarvis.lnk" -ErrorAction SilentlyContinue
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", $null, "User")

Write-Host "Jarvis désinstallé." -ForegroundColor Green
