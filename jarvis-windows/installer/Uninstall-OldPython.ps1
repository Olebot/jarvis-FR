<#
.SYNOPSIS
    Désinstalle toutes les versions de Python détectées sur le volume C:,
    nettoie %APPDATA%\Python, %LOCALAPPDATA%\Programs\Python, pip cache,
    et entrées PATH associées.

.NOTES
    Conserve les Python installés sur d'autres volumes (D:, E:, etc.).
    Demande confirmation utilisateur.
#>

$ErrorActionPreference = "Continue"

Write-Host "Recherche des installations Python sur C:..." -ForegroundColor Cyan

# 1) Désinstallations via le registre Uninstall
$uninstallKeys = @(
    "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
    "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
)

$pythonEntries = foreach ($k in $uninstallKeys) {
    Get-ItemProperty $k -ErrorAction SilentlyContinue |
        Where-Object {
            $_.DisplayName -match '^Python (3|2)\.' -and
            ($_.InstallLocation -like 'C:\*' -or -not $_.InstallLocation)
        }
}

if (-not $pythonEntries) {
    Write-Host "Aucune installation Python détectée sur C:." -ForegroundColor Green
} else {
    Write-Host "`nVersions trouvées :" -ForegroundColor Yellow
    $pythonEntries | ForEach-Object { Write-Host "  - $($_.DisplayName)  ($($_.InstallLocation))" }
    $ok = Read-Host "Désinstaller toutes ces versions ? (O/N)"
    if ($ok -eq "O" -or $ok -eq "o") {
        foreach ($p in $pythonEntries) {
            Write-Host "Désinstallation de $($p.DisplayName)..." -ForegroundColor Yellow
            if ($p.QuietUninstallString) {
                Start-Process "cmd.exe" -ArgumentList "/c $($p.QuietUninstallString)" -Wait -NoNewWindow
            } elseif ($p.UninstallString) {
                # Force silencieux si MSI
                if ($p.UninstallString -match 'msiexec') {
                    $code = ($p.UninstallString -split ' ')[-1]
                    Start-Process "msiexec.exe" -ArgumentList "/x $code /qn" -Wait -NoNewWindow
                } else {
                    Start-Process "cmd.exe" -ArgumentList "/c $($p.UninstallString) /quiet" -Wait -NoNewWindow
                }
            }
        }
    }
}

# 2) Nettoyage répertoires résiduels sur C:
Write-Host "`nNettoyage des dossiers résiduels..." -ForegroundColor Cyan
$pathsToClean = @(
    "$env:LOCALAPPDATA\Programs\Python",
    "$env:APPDATA\Python",
    "$env:LOCALAPPDATA\pip\Cache",
    "$env:USERPROFILE\AppData\Local\pip\cache",
    "C:\Python27", "C:\Python36", "C:\Python37", "C:\Python38",
    "C:\Python39", "C:\Python310", "C:\Python311", "C:\Python312", "C:\Python313"
)

foreach ($p in $pathsToClean) {
    if (Test-Path $p) {
        try {
            Remove-Item -Recurse -Force $p -ErrorAction Stop
            Write-Host "  Supprimé : $p" -ForegroundColor Green
        } catch {
            Write-Host "  Impossible de supprimer : $p ($_)" -ForegroundColor Red
        }
    }
}

# 3) Nettoyage PATH utilisateur
Write-Host "`nNettoyage des entrées PATH liées à Python sur C:..." -ForegroundColor Cyan
foreach ($scope in @('User','Machine')) {
    $path = [Environment]::GetEnvironmentVariable("Path", $scope)
    if ($path) {
        $clean = ($path -split ';') |
            Where-Object { $_ -and -not ($_ -match '^[Cc]:\\.*[Pp]ython') -and -not ($_ -match '^[Cc]:\\.*pip') }
        $newPath = ($clean -join ';')
        if ($newPath -ne $path) {
            [Environment]::SetEnvironmentVariable("Path", $newPath, $scope)
            Write-Host "  PATH ($scope) nettoyé." -ForegroundColor Green
        }
    }
}

Write-Host "`nNettoyage terminé.`n" -ForegroundColor Green
