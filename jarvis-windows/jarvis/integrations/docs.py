"""Google Docs."""
from __future__ import annotations

import logging

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.docs")


class DocsService:
    def __init__(self, auth):
        self.docs = build("docs", "v1", credentials=auth.credentials(), cache_discovery=False)
        self.drive = build("drive", "v3", credentials=auth.credentials(), cache_discovery=False)

    def create(self, title: str, content: str = "") -> str:
        doc = self.docs.documents().create(body={"title": title}).execute()
        doc_id = doc["documentId"]
        if content:
            self.docs.documents().batchUpdate(
                documentId=doc_id,
                body={"requests": [{"insertText": {"location": {"index": 1}, "text": content}}]},
            ).execute()
        return f"https://docs.google.com/document/d/{doc_id}/edit"

    def append(self, doc_id: str, text: str) -> None:
        self.docs.documents().batchUpdate(
            documentId=doc_id,
            body={"requests": [{"insertText": {"endOfSegmentLocation": {}, "text": text}}]},
        ).execute()
