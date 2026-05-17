"""Client LLM cloud (Anthropic / OpenAI / Gemini) avec clé Emergent universelle."""
from __future__ import annotations

import logging
import os
from typing import List, Optional

log = logging.getLogger("jarvis.llm.cloud")

SYSTEM_PROMPT_FR = (
    "Tu es Jarvis, un assistant vocal en français. Réponds de façon concise, "
    "naturelle et chaleureuse. Limite tes réponses à 3 phrases sauf si on te "
    "demande des détails."
)


class CloudLLMClient:
    def __init__(self, cfg):
        self.provider = (cfg.provider or "anthropic").lower()
        self.model = cfg.model
        self.temperature = cfg.get("temperature", 0.7)
        self._history: List[dict] = []
        self._client = None
        self._init_client()

    def _api_key(self) -> Optional[str]:
        emergent = os.environ.get("EMERGENT_LLM_KEY")
        if self.provider == "anthropic":
            return os.environ.get("ANTHROPIC_API_KEY") or emergent
        if self.provider == "openai":
            return os.environ.get("OPENAI_API_KEY") or emergent
        if self.provider == "gemini":
            return os.environ.get("GEMINI_API_KEY") or emergent
        return None

    def _init_client(self):
        key = self._api_key()
        if not key:
            log.warning("Aucune clé API cloud — mode cloud désactivé.")
            return
        try:
            if self.provider == "anthropic":
                import anthropic
                self._client = anthropic.Anthropic(api_key=key)
            elif self.provider == "openai":
                from openai import OpenAI
                self._client = OpenAI(api_key=key)
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=key)
                self._client = genai.GenerativeModel(self.model or "gemini-2.0-flash")
        except Exception as e:
            log.exception("Init client cloud %s : %s", self.provider, e)
            self._client = None

    def chat(self, user_msg: str) -> str:
        if self._client is None:
            return "Le mode cloud n'est pas configuré."

        self._history.append({"role": "user", "content": user_msg})
        try:
            if self.provider == "anthropic":
                reply = self._chat_anthropic(user_msg)
            elif self.provider == "openai":
                reply = self._chat_openai(user_msg)
            elif self.provider == "gemini":
                reply = self._chat_gemini(user_msg)
            else:
                reply = "Provider cloud inconnu."
            self._history.append({"role": "assistant", "content": reply})
            return reply
        except Exception as e:
            log.exception("Erreur LLM cloud : %s", e)
            return "Erreur côté cloud."

    def _chat_anthropic(self, user_msg: str) -> str:
        resp = self._client.messages.create(
            model=self.model or "claude-sonnet-4-5",
            max_tokens=512,
            system=SYSTEM_PROMPT_FR,
            messages=self._history,
            temperature=self.temperature,
        )
        return resp.content[0].text.strip()

    def _chat_openai(self, user_msg: str) -> str:
        msgs = [{"role": "system", "content": SYSTEM_PROMPT_FR}] + self._history
        resp = self._client.chat.completions.create(
            model=self.model or "gpt-4o-mini",
            messages=msgs,
            temperature=self.temperature,
            max_tokens=512,
        )
        return resp.choices[0].message.content.strip()

    def _chat_gemini(self, user_msg: str) -> str:
        chat = self._client.start_chat(history=[])
        prompt = f"{SYSTEM_PROMPT_FR}\n\nUtilisateur : {user_msg}"
        resp = chat.send_message(prompt)
        return resp.text.strip()
