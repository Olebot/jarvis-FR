# Voix de référence pour XTTS-v2

Placez dans ce dossier un fichier `sample_fr.wav` :
- Format : WAV mono, 22050 Hz ou 16000 Hz
- Durée : 6 à 12 secondes
- Contenu : votre voix (ou la voix à cloner) lisant un texte naturel en français

XTTS-v2 clonera ce timbre vocal pour toutes les réponses de Jarvis.

## Exemple de phrase à enregistrer

> "Bonjour, je m'appelle ... et je teste la synthèse vocale pour mon assistant
> Jarvis. La voix doit sembler naturelle, posée, et bien articulée."

## Si vous n'avez pas d'échantillon

Mettez `speaker_wav: null` dans `config.yaml` : XTTS-v2 utilisera alors sa
voix française par défaut (moins personnalisée mais fonctionnelle).
