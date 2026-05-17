"""Authentification OAuth Google (Installed Application flow)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

log = logging.getLogger("jarvis.google")


class GoogleAuth:
    def __init__(self, cfg):
        from jarvis.config import ROOT
        self.cfg = cfg
        self.client_secret = Path(cfg.client_secret_file)
        if not self.client_secret.is_absolute():
            self.client_secret = ROOT / self.client_secret
        self.token_file = Path(cfg.token_file)
        if not self.token_file.is_absolute():
            self.token_file = ROOT / self.token_file
        self.scopes = list(cfg.scopes or [])
        self._creds: Optional[Credentials] = None

    def ensure_credentials(self) -> Credentials:
        if self._creds and self._creds.valid:
            return self._creds

        if self.token_file.exists():
            self._creds = Credentials.from_authorized_user_info(
                json.loads(self.token_file.read_text(encoding="utf-8")),
                scopes=self.scopes,
            )
        if self._creds and self._creds.expired and self._creds.refresh_token:
            try:
                self._creds.refresh(Request())
            except Exception:
                self._creds = None
        if not self._creds or not self._creds.valid:
            if not self.client_secret.exists():
                raise FileNotFoundError(
                    f"client_secret.json absent : {self.client_secret}\n"
                    "Voir README §3 pour le créer via Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.client_secret), self.scopes
            )
            self._creds = flow.run_local_server(port=0, open_browser=True)
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            self.token_file.write_text(self._creds.to_json(), encoding="utf-8")
            log.info("Token OAuth sauvegardé : %s", self.token_file)
        return self._creds

    def credentials(self) -> Credentials:
        return self.ensure_credentials()
