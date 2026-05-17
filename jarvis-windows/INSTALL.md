# Jarvis FR — Guide d'installation détaillé (Windows 11 + RTX 3070)

Version : **Python 3.12.7** + **CUDA 12.1** + **coqui-tts** fork + **faster-whisper 1.1**
Cible : NVIDIA GeForce RTX 3070 Laptop GPU (8 Go VRAM)
Durée totale : **30 à 60 min** (selon connexion internet)
Espace requis sur disque cible : **~25 Go** (Python ~500 Mo + venv ~6 Go + XTTS ~2 Go + Whisper large-v3 ~3 Go + Ollama Llama 3.1 8B ~5 Go + chromium Playwright ~500 Mo + marge)

---

## ÉTAPE 0 — Vérifications préalables (5 min)

### 0.1 Pilote NVIDIA récent
1. Touche **Windows** → tapez `Informations système NVIDIA` → ouvrir
2. Vérifiez **Pilote ≥ 555.85** (recommandé 560+)
3. Sinon : téléchargez le dernier pilote **Game Ready** ou **Studio** :
   https://www.nvidia.com/Download/index.aspx (GeForce RTX 3070 Laptop)

### 0.2 Test rapide CUDA
Ouvrez **PowerShell** (utilisateur normal) :
```powershell
nvidia-smi
```
Doit afficher votre RTX 3070 et `CUDA Version: 12.x`. Si la commande n'existe pas, le pilote n'est pas installé.

### 0.3 Espace disque
Touche Windows → `Stockage` → vérifiez qu'au moins **25 Go libres** sur le disque cible (D:, E:, etc.). Idéalement 40 Go pour confort.

### 0.4 Microphone fonctionnel
Touche Windows → `Paramètres son` → `Entrée` → testez le niveau d'entrée en parlant. Notez le nom du micro (sera utilisé plus tard si besoin).

---

## ÉTAPE 1 — Création du projet Google Cloud (10 min, à faire en parallèle pendant l'installation)

Cette étape est **obligatoire** pour Gmail, Drive, Calendar, Docs, Sheets et Photos.

### 1.1 Créer le projet
1. https://console.cloud.google.com/ → connectez-vous
2. En haut, **menu projets** → **Nouveau projet**
   - Nom : `Jarvis-FR`
   - Créer

### 1.2 Activer les APIs (une par une)
Menu hamburger → **APIs et services** → **Bibliothèque**. Recherchez puis cliquez **Activer** pour chacune :
- [ ] **Gmail API**
- [ ] **Google Drive API**
- [ ] **Google Calendar API**
- [ ] **Google Docs API**
- [ ] **Google Sheets API**
- [ ] **Photos Library API**

### 1.3 Configurer l'écran de consentement OAuth
1. **APIs et services** → **Écran de consentement OAuth**
2. **Type d'utilisateur** : `Externe` (sauf si Google Workspace)
3. Remplir :
   - Nom de l'application : `Jarvis`
   - Email d'assistance : votre email
   - Coordonnées du développeur : votre email
   - Cliquez **Enregistrer et continuer**
4. **Champs d'application** : laissez vide → Continuer
5. **Utilisateurs de test** → **Ajouter** → entrez votre email Google → Enregistrer
6. **Résumé** → terminer

### 1.4 Créer les identifiants OAuth Desktop
1. **APIs et services** → **Identifiants** → **+ Créer des identifiants** → **ID client OAuth**
2. **Type d'application** : `Application de bureau`
3. Nom : `Jarvis Desktop`
4. **Créer** → un popup affiche l'ID client → **Télécharger JSON**
5. Renommez le fichier en **`client_secret.json`** et gardez-le de côté (vous le placerez à l'étape 4.1)

---

## ÉTAPE 2 — Téléchargement du projet (1 min)

Récupérez le dossier `/app/jarvis-windows/` complet depuis Emergent (via "Download code" ou Git push). Vous obtenez localement :
```
C:\Users\<vous>\Downloads\jarvis-windows\
├── installer\
├── jarvis\
├── config\
├── voices\
└── README.md
```

> Vous pouvez le copier ailleurs (ex. `C:\Temp\jarvis-windows\`), peu importe — il sera **recopié** sur votre disque cible par l'installeur.

---

## ÉTAPE 3 — Exécution de l'installeur (20 à 40 min)

### 3.1 Lancer PowerShell en administrateur
1. Touche Windows → tapez `powershell`
2. Clic droit sur **Windows PowerShell** → **Exécuter en tant qu'administrateur**
3. Validez l'UAC

### 3.2 Autoriser les scripts pour la session
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

### 3.3 Aller dans le dossier installer
```powershell
cd C:\Users\<vous>\Downloads\jarvis-windows\installer
```

### 3.4 Lancer l'installeur
```powershell
.\Install-Jarvis.ps1
```

### 3.5 Le script vous pose 3 questions

**Q1 — Choix du disque cible**
Le script affiche la liste des volumes avec ≥ 40 Go libres (hors C:). Tapez la lettre (ex. `D`).

**Q2 — Confirmation `D:\Jarvis`**
Tapez `O` pour confirmer (tout sera dans `<DISQUE>:\Jarvis\`).

**Q3 — Désinstallation Python sur C:**
Tapez `O` (recommandé pour libérer C:).
Si plusieurs Python sont détectés sur C:, un sous-script liste les versions et redemande confirmation.

### 3.6 Ce que fait le script automatiquement
Vous pouvez aller boire un café ☕ — il va :
1. Désinstaller tous les Python C: + nettoyer PATH + caches pip
2. Télécharger et installer **Python 3.12.7** dans `<DISQUE>:\Jarvis\python312\`
3. Créer le venv dans `<DISQUE>:\Jarvis\venv\`
4. Installer **torch 2.5.1 + torchaudio + CUDA 12.1** (~2 Go)
5. Installer **coqui-tts**, **faster-whisper**, Google APIs, Playwright, pycaw, etc.
6. Télécharger **Chromium** pour Playwright (~150 Mo)
7. Installer **Ollama** + configurer `OLLAMA_MODELS` sur `<DISQUE>:\Jarvis\ollama\models\`
8. Copier le code Jarvis dans `<DISQUE>:\Jarvis\jarvis\`
9. Vous demander le modèle Ollama → tapez `Entrée` pour `llama3.1:8b` par défaut → téléchargement ~5 Go
10. Créer `start-jarvis.bat` + raccourci Bureau **Jarvis**

### 3.7 Messages à surveiller
- ✅ `Python 3.12 installé`
- ✅ `XTTS-v2 prêt` (au premier lancement seulement)
- ✅ `Installation terminée`
- ❌ Si erreur `CUDA not available` lors de l'install torch : vérifiez `nvidia-smi` (étape 0.2) puis relancez

---

## ÉTAPE 4 — Configuration finale (5 min)

### 4.1 Placer `client_secret.json`
Copiez le fichier téléchargé à l'étape 1.4 vers :
```
<DISQUE>:\Jarvis\config\client_secret.json
```

### 4.2 (Optionnel) Clé LLM cloud
Si vous voulez le mode hybride local/cloud, éditez `<DISQUE>:\Jarvis\config\.env` :
```ini
# Une seule des trois suffit :
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
GEMINI_API_KEY=AIza...

# OU la clé universelle Emergent (couvre Claude/GPT/Gemini)
EMERGENT_LLM_KEY=sk-emergent-...
```

### 4.3 (Optionnel mais recommandé) Échantillon vocal pour clonage
Pour que Jarvis parle avec **votre voix** :
1. Enregistrez **6 à 12 secondes** de votre voix lisant un texte naturel français (Audacity, voice recorder Windows, etc.)
2. Exportez en **WAV mono 22050 Hz**
3. Nommez le fichier `sample_fr.wav` et placez-le dans `<DISQUE>:\Jarvis\voices\`

Sans échantillon : éditez `<DISQUE>:\Jarvis\config\config.yaml` et mettez `speaker_wav: null` → voix française par défaut de XTTS-v2.

### 4.4 (Optionnel) Personnaliser `config.yaml`
Ouvrez `<DISQUE>:\Jarvis\config\config.yaml` :
```yaml
A:
  wake_word: "jarvis"        # mettre "" pour désactiver le mot d'éveil
  greeting: "Bonjour ..."    # phrase de bienvenue
llm:
  mode: "hybrid"             # local | cloud | hybrid
  local:
    model: "llama3.1:8b"     # ou mistral:7b, qwen2.5:7b
deezer:
  default_target: "ask"      # desktop | web | ask
```

---

## ÉTAPE 5 — Premier lancement (5 min)

### 5.1 Double-cliquez sur le raccourci Bureau **Jarvis**

OU bien en ligne de commande :
```powershell
<DISQUE>:\Jarvis\start-jarvis.bat
```

### 5.2 Première fois (uniquement) — autorisation Google
- Votre **navigateur s'ouvre automatiquement**
- Connectez-vous avec votre compte Google
- Écran "Google n'a pas validé cette application" → cliquez **Paramètres avancés** → **Accéder à Jarvis (non sécurisé)**
- Cochez toutes les autorisations demandées → **Continuer**
- Le token est sauvegardé dans `config\google_token.json` (chiffré DPAPI)

### 5.3 Première fois — téléchargement modèles IA
La première exécution télécharge :
- **XTTS-v2** (~2 Go) — modèle Coqui
- **Whisper large-v3** (~3 Go) — modèle CTranslate2

Patientez avec la console ouverte. Aux exécutions suivantes : démarrage en **5 à 10 sec**.

### 5.4 Jarvis vous parle
Vous entendez : *« Bonjour, je suis Jarvis. Je vous écoute. »*
Une icône **J** apparaît dans la zone de notification.

### 5.5 Premier test vocal
Parlez clairement dans le micro :
> *« Jarvis, quelle heure est-il ? »*

Jarvis doit répondre l'heure actuelle.

---

## ÉTAPE 6 — Commandes vocales à tester

### Système
- *« Jarvis, ouvre le Bloc-notes »*
- *« Mets le volume à 40 pour cent »*
- *« Prends une capture d'écran »*
- *« Quel est le niveau de batterie ? »*

### Deezer (lancez d'abord l'app ou demandez à Jarvis)
- *« Jarvis, ouvre Deezer sur le bureau »* (ou *« dans le navigateur »*)
- *« Joue »*, *« Pause »*, *« Piste suivante »*

### Google
- *« Lis mes derniers e-mails »*
- *« Quels sont mes rendez-vous aujourd'hui ? »*
- *« Cherche dans Drive le document Budget »*

### Conversation libre (LLM)
- *« Jarvis, explique-moi la mécanique quantique »* → Ollama local
- *« Jarvis, en mode cloud, écris-moi un poème »* → bascule cloud

---

## DÉPANNAGE — Problèmes fréquents

### A. "CUDA out of memory" lors de la synthèse
Éditez `config.yaml` :
```yaml
tts:
  precision: "float32"    # au lieu de float16 si bug
stt:
  model: "medium"         # au lieu de large-v3 (économise ~2 Go VRAM)
```

### B. Jarvis ne m'entend pas
1. Vérifiez le micro par défaut : `Paramètres son → Entrée`
2. Dans `config.yaml`, listez les périphériques :
   ```powershell
   <DISQUE>:\Jarvis\venv\Scripts\python.exe -c "import sounddevice; print(sounddevice.query_devices())"
   ```
3. Mettez l'**index** du bon micro dans `stt.input_device` du `config.yaml`

### C. XTTS-v2 silence sans erreur
Vérifiez la sortie audio par défaut Windows. Ou forcez l'output dans `config.yaml` :
```yaml
tts:
  output_device: 5    # index du haut-parleur
```

### D. Ollama "connection refused"
Ouvrez PowerShell et lancez manuellement :
```powershell
ollama serve
```
Dans une autre fenêtre :
```powershell
ollama pull llama3.1:8b
ollama run llama3.1:8b "Bonjour"
```

### E. Google OAuth "Accès bloqué"
Retournez à l'écran de consentement (étape 1.3) et ajoutez votre email comme **Utilisateur test**. L'app reste en mode "test" tant que vous ne la publiez pas — c'est normal.

### F. Deezer Web : pas connecté
Au premier *« ouvre Deezer dans le navigateur »*, le Chromium Playwright s'ouvre — connectez-vous manuellement à votre compte Deezer. Le profil est sauvegardé dans `config\deezer_chromium\` pour les fois suivantes.

### G. Latence TTS élevée (>3 sec)
- Vérifiez que CUDA est bien utilisé : pendant la synthèse, `nvidia-smi` doit montrer le process python.
- Si ça reste lent, passez à un modèle plus léger : `stt.model: "small"`
- En cas de torch CPU détecté par erreur :
  ```powershell
  <DISQUE>:\Jarvis\venv\Scripts\pip install --force-reinstall torch==2.5.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
  ```

### H. "ModuleNotFoundError: TTS"
`coqui-tts` expose le module sous le nom `TTS` (compatible avec l'API officielle). Si le module manque, réinstallez :
```powershell
<DISQUE>:\Jarvis\venv\Scripts\pip install --force-reinstall coqui-tts==0.25.3
```

### I. Le script PowerShell refuse de démarrer
- Vous n'êtes pas en admin → relancez PowerShell **en tant qu'administrateur**
- Politique d'exécution bloquée : `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force`

---

## DÉSINSTALLATION COMPLÈTE

```powershell
cd <DISQUE>:\Jarvis\installer
.\Uninstall-Jarvis.ps1
```

Le script :
- Arrête le processus Ollama
- Supprime tout `<DISQUE>:\Jarvis\`
- Supprime le raccourci Bureau
- Nettoie la variable d'environnement `OLLAMA_MODELS`

---

## RÉSUMÉ — Checklist d'installation

- [ ] Pilote NVIDIA ≥ 555 installé
- [ ] `nvidia-smi` fonctionne et montre la RTX 3070
- [ ] ≥ 25 Go libres sur disque cible
- [ ] Projet Google Cloud créé, 6 APIs activées
- [ ] `client_secret.json` téléchargé
- [ ] Email ajouté comme utilisateur test OAuth
- [ ] Projet `jarvis-windows/` téléchargé localement
- [ ] PowerShell **admin** + `Set-ExecutionPolicy Bypass`
- [ ] `.\Install-Jarvis.ps1` exécuté avec succès
- [ ] `client_secret.json` placé dans `<DISQUE>:\Jarvis\config\`
- [ ] (Optionnel) `sample_fr.wav` placé dans `voices\`
- [ ] (Optionnel) Clé LLM cloud dans `.env`
- [ ] Double-clic sur raccourci **Jarvis** → ça parle ! 🎉
