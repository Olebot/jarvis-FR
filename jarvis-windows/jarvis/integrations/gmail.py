"""Gmail : lister, lire, envoyer."""
from __future__ import annotations

import base64
import logging
from email.mime.text import MIMEText
from typing import List

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.gmail")


class GmailService:
    def __init__(self, auth):
        self.service = build("gmail", "v1", credentials=auth.credentials(), cache_discovery=False)

    def list_recent(self, max_results: int = 5) -> List[dict]:
        resp = self.service.users().messages().list(
            userId="me", maxResults=max_results, q="in:inbox -category:promotions"
        ).execute()
        ids = [m["id"] for m in resp.get("messages", [])]
        out = []
        for mid in ids:
            msg = self.service.users().messages().get(
                userId="me", id=mid, format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"].get("headers", [])}
            out.append({
                "id": mid,
                "from": headers.get("From", "?"),
                "subject": headers.get("Subject", "(sans objet)"),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
            })
        return out

    def send(self, to: str, subject: str, body: str) -> str:
        msg = MIMEText(body, _charset="utf-8")
        msg["to"] = to
        msg["subject"] = subject
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")
        sent = self.service.users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return sent["id"]
