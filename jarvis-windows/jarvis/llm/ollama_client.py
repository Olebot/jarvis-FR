"""Client LLM local via Ollama (HTTP)."""
from __future__ import annotations

import logging
from typing import List

import requests

log = logging.getLogger("jarvis.llm.ollama")


SYSTEM_PROMPT_FR = (
    "Tu es Jarvis, un assistant vocal en français. Réponds de façon concise, "
    "naturelle et chaleureuse. Évite les listes à puces ; parle comme un humain. "
    "Limite tes réponses à 3 phrases sauf si on te demande des détails."
)


class OllamaClient:
    def __init__(self, cfg):
        self.cfg = cfg
        self.model = cfg.model or "llama3.1:8b"
        self.base_url = (cfg.base_url or "http://localhost:11434").rstrip("/")
        self.temperature = cfg.get("temperature", 0.7)
        self._history: List[dict] = [{"role": "system", "content": SYSTEM_PROMPT_FR}]

    def chat(self, user_msg: str) -> str:
        self._history.append({"role": "user", "content": user_msg})
        try:
            r = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": self._history,
                    "stream": False,
                    "options": {"temperature": self.temperature},
                },
                timeout=60,
            )
            r.raise_for_status()
            data = r.json()
            reply = data.get("message", {}).get("content", "").strip()
            self._history.append({"role": "assistant", "content": reply})
            # Évite l'enflure de contexte
            if len(self._history) > 21:
                self._history = [self._history[0]] + self._history[-20:]
            return reply
        except Exception as e:
            log.exception("Ollama indisponible : %s", e)
            return "Je n'arrive pas à joindre le modèle local."
