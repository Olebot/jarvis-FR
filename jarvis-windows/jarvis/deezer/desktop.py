"""Contrôle de l'application Deezer Bureau Windows.

Utilise des raccourcis clavier média globaux (compatibles avec Deezer Bureau)
et lance/ferme l'exécutable.
"""
from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

import psutil

log = logging.getLogger("jarvis.deezer.desktop")


class DeezerDesktop:
    def __init__(self, cfg):
        self.cfg = cfg
        self.exe_path = self._resolve_exe(cfg.desktop_exe)

    def _resolve_exe(self, raw: str) -> Path:
        if not raw:
            return Path("")
        # Remplace les variables d'environnement Windows
        expanded = os.path.expandvars(raw)
        return Path(expanded)

    def is_running(self) -> bool:
        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] and p.info["name"].lower().startswith("deezer"):
                    return True
            except Exception:
                continue
        return False

    def launch(self) -> bool:
        if self.is_running():
            return True
        if self.exe_path and self.exe_path.exists():
            subprocess.Popen([str(self.exe_path)])
            return True
        log.warning("Deezer.exe introuvable : %s", self.exe_path)
        return False

    def close(self) -> None:
        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] and p.info["name"].lower().startswith("deezer"):
                    p.terminate()
            except Exception:
                continue

    # ---- Contrôles via touches média globales ----
    def _send_media_key(self, key: str) -> None:
        try:
            import keyboard
            keyboard.send(key)
        except Exception as e:
            log.exception("Échec envoi touche média %s : %s", key, e)

    def play(self):       self._send_media_key("play/pause media")
    def pause(self):      self._send_media_key("play/pause media")
    def next_track(self): self._send_media_key("next track")
    def prev_track(self): self._send_media_key("previous track")
