# PRD — Jarvis FR (Assistant vocal Windows 11)

## Problème original
> construis moi un jarvis parlant français, avec synthèse vocale en local,
> utilisation de google drive, photos, calendar, docs, sheets, gmail, utilisation
> au choix de l'application de bureau deezer ou deezer en navigateur,
> commandant windows 11. Avec au moins la partie synthèse vocale fonctionnant
> sur le processeur graphique NVIDIA GeForce RTX 3070 Laptop GPU, avec le
> maximum d'installation sur un disque de mon choix à l'installation, libérant
> au maximum l'utilisation du volume contenant windows. À l'installation,
> désinstaller versions précédentes de python avec dépendances existantes sur
> le volume windows pour une installation propre.

## Choix utilisateur retenus
- Livrable : projet **Python desktop** (code source + script PowerShell)
- TTS : **Coqui XTTS-v2** sur CUDA (RTX 3070)
- LLM : **Ollama local** + **cloud** (mode hybride basculable)
- Google : OAuth standard (`client_secret.json` fourni par l'utilisateur)
- Deezer : Bureau + Web au choix vocal

## Architecture livrée (`/app/jarvis-windows/`)
- `installer/Install-Jarvis.ps1` — installeur principal (désinstalle Python C:, installe Python 3.11 + venv + torch CUDA 12.1 + XTTS + faster-whisper + Ollama sur disque choisi)
- `installer/Uninstall-OldPython.ps1` — nettoyage Python existants sur C:
- `installer/Uninstall-Jarvis.ps1` — désinstallation complète
- `jarvis/tts/xtts_engine.py` — XTTS-v2 GPU
- `jarvis/stt/whisper_engine.py` — faster-whisper CUDA + VAD
- `jarvis/llm/{ollama_client,cloud_client,router}.py` — LLM hybride
- `jarvis/integrations/{google_auth,gmail,drive,calendar_api,docs,sheets,photos}.py`
- `jarvis/deezer/{desktop,web}.py` — Deezer app + automation Playwright
- `jarvis/windows/controller.py` — volume (pycaw), veille, capture, lancement apps
- `jarvis/core/{assistant,command_router}.py` — orchestration et intents FR
- `jarvis/ui/tray.py` — icône zone de notification
- `config/config.example.yaml`, `config/.env.example`
- `README.md` — guide installation/usage/dépannage

## Fonctionnalités implémentées (P0)
- [x] Synthèse vocale française GPU (XTTS-v2 CUDA, FP16)
- [x] Reconnaissance vocale française GPU (faster-whisper large-v3)
- [x] LLM local Ollama + cloud (Claude/GPT/Gemini) avec routeur hybride
- [x] Installation sur disque choisi, désinstallation Python C: existant
- [x] Intégrations Google : Drive, Calendar, Docs, Sheets, Gmail, Photos
- [x] Deezer Bureau (touches média) + Deezer Web (Playwright)
- [x] Commandes Windows 11 (volume, veille, arrêt, capture, lancement apps)
- [x] Routeur d'intents français par regex + fallback LLM conversationnel
- [x] Tray icon Windows

## P1 — Améliorations futures
- Wake word offline (Porcupine / openWakeWord) au lieu de regex
- Streaming TTS (lecture pendant génération) pour latence ↓
- Mémoire long terme (résumés conversation sauvegardés)
- Commandes Spotify, WhatsApp, Discord
- UI mini-overlay avec waveform pendant l'écoute
- Auto-update via GitHub Releases

## P2 — Idées
- Mode "réunion" (résumé audio en direct)
- Plugin OBS pour streamers
- Application mobile companion (réveil / commandes à distance)

## Notes techniques
- **Important** : Ce projet ne peut pas être exécuté/testé dans cet
  environnement Linux cloud — il cible Windows 11 + RTX 3070. La validation
  finale se fait sur la machine de l'utilisateur après installation.
- Le lint Python (ruff) passe sur tous les fichiers du projet.
- Toutes les commandes vocales sont en français.
- Le projet est conçu pour libérer au maximum le volume C: : Python, venv,
  modèles XTTS (~2 Go), modèles Whisper (~3 Go), modèles Ollama (~5 Go) sont
  tous installés sur le disque cible.
