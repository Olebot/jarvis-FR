"""Boucle principale de l'assistant : STT → Router/LLM → TTS."""
from __future__ import annotations

import logging
import threading
import time
from typing import Optional

from jarvis.tts.xtts_engine import XTTSEngine
from jarvis.stt.whisper_engine import WhisperEngine
from jarvis.llm.router import LLMRouter
from jarvis.core.command_router import CommandRouter

log = logging.getLogger("jarvis.core")


class Assistant:
    def __init__(self, cfg):
        self.cfg = cfg
        self.running = False
        self._lock = threading.Lock()

        log.info("Initialisation TTS XTTS-v2...")
        self.tts = XTTSEngine(cfg.tts)

        log.info("Initialisation STT faster-whisper...")
        self.stt = WhisperEngine(cfg.stt)

        log.info("Initialisation LLM (mode: %s)...", cfg.llm.mode)
        self.llm = LLMRouter(cfg.llm)

        log.info("Initialisation routeur de commandes...")
        self.commands = CommandRouter(cfg, llm=self.llm)

    def speak(self, text: str) -> None:
        with self._lock:
            log.info("[Jarvis] %s", text)
            self.tts.speak(text)

    def listen_once(self, timeout: float = 8.0) -> Optional[str]:
        return self.stt.listen(timeout=timeout)

    def handle_utterance(self, text: str) -> None:
        if not text:
            return
        log.info("[Utilisateur] %s", text)

        # Mot d'éveil (si configuré)
        wake = (self.cfg.A.wake_word or "").lower().strip()
        text_lower = text.lower()
        if wake and wake not in text_lower:
            log.debug("Wake word absent, ignoré.")
            return
        if wake:
            text = text_lower.replace(wake, "", 1).strip(" ,.!?")

        # Routeur de commandes : essaye d'abord les intents système/Google/Deezer
        handled, reply = self.commands.route(text)
        if not handled:
            # Fallback : conversation libre via LLM
            reply = self.llm.chat(text)

        if reply:
            self.speak(reply)

    def run(self) -> None:
        self.running = True
        greeting = self.cfg.A.greeting or "Bonjour."
        self.speak(greeting)

        while self.running:
            try:
                utterance = self.listen_once(timeout=10.0)
                if utterance:
                    self.handle_utterance(utterance)
                else:
                    time.sleep(0.1)
            except Exception as e:
                log.exception("Erreur dans la boucle principale : %s", e)
                time.sleep(0.5)

    def stop(self) -> None:
        self.running = False
        try:
            self.stt.close()
        except Exception:
            pass
