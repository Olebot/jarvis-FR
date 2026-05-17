"""Routeur LLM : choisit local (Ollama) ou cloud selon le mode et la requête."""
from __future__ import annotations

import logging

from jarvis.llm.ollama_client import OllamaClient
from jarvis.llm.cloud_client import CloudLLMClient

log = logging.getLogger("jarvis.llm.router")


class LLMRouter:
    def __init__(self, cfg):
        self.cfg = cfg
        self.mode = (cfg.mode or "hybrid").lower()
        self.cloud_keywords = [k.lower() for k in (cfg.routing.cloud_keywords or [])]
        self.local = OllamaClient(cfg.local) if self.mode in ("local", "hybrid") else None
        self.cloud = CloudLLMClient(cfg.cloud) if self.mode in ("cloud", "hybrid") else None

    def chat(self, user_msg: str) -> str:
        if self.mode == "local":
            return self.local.chat(user_msg)
        if self.mode == "cloud":
            return self.cloud.chat(user_msg)

        # Hybride : cloud si mots-clés détectés, sinon local
        msg_lower = user_msg.lower()
        use_cloud = any(k in msg_lower for k in self.cloud_keywords)
        if use_cloud and self.cloud is not None:
            log.debug("Routage cloud (mot-clé détecté).")
            return self.cloud.chat(user_msg)
        return self.local.chat(user_msg)
