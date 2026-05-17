# Jarvis FR — Assistant Vocal Windows 11 (XTTS-v2 GPU + Ollama + Google + Deezer)

Assistant vocal francophone local pour Windows 11, conçu pour tirer parti de votre **NVIDIA GeForce RTX 3070 Laptop GPU**.  
Synthèse vocale **Coqui XTTS-v2** sur CUDA, reconnaissance vocale **faster-whisper** GPU, cerveau **Ollama local** (Llama 3 / Mistral) avec basculement **cloud** (Claude / GPT / Gemini), contrôle Windows 11, intégrations **Google** (Drive, Photos, Calendar, Docs, Sheets, Gmail), et pilotage **Deezer Bureau ou Web** sur commande vocale.

> **Important** : Ce projet est livré comme **code source à installer chez vous**. Le script `Install-Jarvis.ps1` désinstallera proprement les anciennes versions de Python du volume Windows (C:) puis installera **Python 3.12**, **Ollama**, les modèles IA et toutes les dépendances sur le **disque de votre choix** (D:, E:, etc.) afin de libérer au maximum le volume Windows.
>
> **Choix Python 3.12** : compromis optimal stabilité/perf en 2026. Python 3.13 n'est pas (encore) viable car `ctranslate2` (cœur de faster-whisper GPU) n'a pas de wheels CUDA pour 3.13.

---

## 1. Prérequis matériels et logiciels

| Composant | Exigence |
|---|---|
| OS | Windows 11 (64 bits) à jour |
| GPU | NVIDIA RTX 3070 Laptop (8 Go VRAM) ou supérieur, drivers ≥ 555.x |
| CUDA | CUDA 13.0 (les wheels PyTorch embarquent les libs nécessaires) ; pilote ≥ 565 |
| Disque cible | ≥ 40 Go libres (modèles XTTS-v2 + Whisper + Ollama Llama 3 8B) |
| Microphone | Tout micro USB ou intégré |
| Compte Google | Pour Drive/Photos/Calendar/Docs/Sheets/Gmail |
| Deezer | Application Bureau Windows installée **et/ou** abonnement Web |

---

## 2. Installation rapide (PowerShell, en administrateur)

1. Téléchargez ce dossier `jarvis-windows/` sur votre PC.
2. Ouvrez **PowerShell en administrateur**.
3. Autorisez les scripts pour cette session :
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   ```
4. Lancez l'installeur :
   ```powershell
   cd C:\chemin\vers\jarvis-windows\installer
   .\Install-Jarvis.ps1
   ```
5. Le script vous demande :
   - **Lettre du disque cible** (ex. `D`) — tout sera installé là (Python, venv, modèles, Ollama).
   - Confirmation de la **désinstallation des Python existants** sur `C:`.
   - **Modèle Ollama** à télécharger (recommandé : `llama3.1:8b` ou `mistral:7b`).

Durée totale : 20 à 45 min selon votre connexion (téléchargement modèles ~ 6 Go).

---

## 3. Configuration Google OAuth (à faire une fois)

1. Allez sur https://console.cloud.google.com/
2. Créez un projet (ou réutilisez-en un).
3. Activez les APIs suivantes :
   - Gmail API
   - Google Drive API
   - Google Calendar API
   - Google Docs API
   - Google Sheets API
   - Photos Library API
4. **Identifiants → Créer des identifiants → ID client OAuth → Application de bureau**.
5. Téléchargez le fichier JSON et renommez-le `client_secret.json`.
6. Placez-le dans `<DISQUE>:\Jarvis\config\client_secret.json`.
7. Au premier lancement, Jarvis ouvrira votre navigateur pour vous demander l'accord OAuth.

---

## 4. Configuration LLM hybride

Éditez `<DISQUE>:\Jarvis\config\config.yaml` :

```yaml
llm:
  mode: hybrid          # local | cloud | hybrid
  local:
    provider: ollama
    model: llama3.1:8b
    base_url: http://localhost:11434
  cloud:
    provider: anthropic # anthropic | openai | gemini
    model: claude-sonnet-4-5
    api_key: ""         # ou utiliser EMERGENT_LLM_KEY
  routing:
    # En mode hybride : local par défaut, cloud si la requête contient ces mots-clés
    cloud_keywords: ["recherche web", "actualité", "raisonnement long", "code complexe"]
```

---

## 5. Lancement

Double-cliquez sur le raccourci **Jarvis** créé sur le Bureau, ou bien :
```powershell
<DISQUE>:\Jarvis\start-jarvis.bat
```

Une icône apparaît dans la **zone de notification**. Jarvis dit *« Bonjour, je suis Jarvis. Je vous écoute. »*

---

## 6. Commandes vocales (exemples français)

### Système Windows 11
- *« Jarvis, ouvre le Bloc-notes / Chrome / l'Explorateur »*
- *« Mets le volume à 30 pour cent »*, *« Coupe le son »*, *« Augmente le volume »*
- *« Verrouille l'ordinateur »*, *« Mets en veille »*, *« Éteins l'ordinateur dans 10 minutes »*
- *« Quelle heure est-il ? »*, *« Quel est le niveau de batterie ? »*
- *« Prends une capture d'écran »*

### Deezer (au choix)
- *« Jarvis, lance Deezer sur le bureau »* → ouvre l'app Deezer Windows
- *« Jarvis, ouvre Deezer dans le navigateur »* → ouvre deezer.com
- *« Joue / Pause / Piste suivante / Piste précédente »* (fonctionne pour les deux)
- *« Joue la playlist Chill »* (Deezer Web uniquement, via automation)

### Google
- *« Lis mes derniers e-mails »*, *« Envoie un mail à Jean : Réunion repoussée à 15h »*
- *« Quels sont mes rendez-vous aujourd'hui ? »*, *« Ajoute une réunion demain à 14h : Point projet »*
- *« Cherche dans Drive le document Budget 2026 »*
- *« Crée un Google Doc intitulé Compte-rendu réunion »*
- *« Ouvre la dernière feuille de calcul »*
- *« Montre-moi mes photos du week-end dernier »*

### Conversation libre
- *« Jarvis, explique-moi la mécanique quantique »* → LLM local Ollama
- *« Jarvis, en mode cloud, écris-moi un poème »* → bascule cloud

---

## 7. Architecture du projet

```
jarvis-windows/
├── installer/
│   ├── Install-Jarvis.ps1            # Installeur principal
│   ├── Uninstall-OldPython.ps1       # Nettoyage Python existants
│   └── requirements.txt              # Dépendances Python
├── jarvis/
│   ├── main.py                       # Point d'entrée
│   ├── config.py                     # Chargement config.yaml + .env
│   ├── core/
│   │   ├── assistant.py              # Boucle principale STT→LLM→TTS
│   │   └── command_router.py         # Détection intents français
│   ├── tts/xtts_engine.py            # Coqui XTTS-v2 sur CUDA
│   ├── stt/whisper_engine.py         # faster-whisper GPU
│   ├── llm/
│   │   ├── ollama_client.py
│   │   ├── cloud_client.py
│   │   └── router.py                 # Routage hybride
│   ├── integrations/
│   │   ├── google_auth.py
│   │   ├── gmail.py, drive.py, calendar_api.py
│   │   ├── docs.py, sheets.py, photos.py
│   ├── deezer/
│   │   ├── desktop.py                # Contrôle app Deezer Windows
│   │   └── web.py                    # Automation deezer.com
│   ├── windows/controller.py         # Commandes Windows 11
│   └── ui/tray.py                    # Icône zone de notification
├── config/
│   ├── config.example.yaml
│   └── .env.example
├── voices/
│   └── (placez ici un échantillon WAV de votre voix pour clonage XTTS)
└── README.md
```

---

## 8. Dépannage rapide

| Problème | Solution |
|---|---|
| `CUDA out of memory` | Réduisez la qualité TTS : `tts.precision: float16` dans `config.yaml` |
| XTTS-v2 lent | Vérifiez `nvidia-smi` ; si CPU utilisé, réinstallez torch CUDA : `pip install torch==2.11.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu130` |
| Ollama ne répond pas | `ollama serve` dans un terminal séparé, puis `ollama pull llama3.1:8b` |
| Pas de son | Vérifiez le périphérique de sortie par défaut dans Windows |
| Google OAuth bloqué | Ajoutez votre email comme « Utilisateur test » dans l'écran de consentement OAuth |
| Deezer Web ne se connecte pas | Lancez `playwright install chromium` puis connectez-vous manuellement au premier lancement |

---

## 9. Désinstallation

```powershell
cd <DISQUE>:\Jarvis\installer
.\Uninstall-Jarvis.ps1
```

---

## 10. Sécurité et vie privée

- **Aucune donnée vocale n'est envoyée dans le cloud** sauf si vous activez le mode `cloud` explicitement.
- Les credentials Google et clés API sont stockés **localement** dans `<DISQUE>:\Jarvis\config\`.
- Le token OAuth est chiffré par Windows DPAPI.

---

Bonne discussion avec votre Jarvis ! 🤖🇫🇷
