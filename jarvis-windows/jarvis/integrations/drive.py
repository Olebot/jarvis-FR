"""Google Drive."""
from __future__ import annotations

import logging
from typing import List

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.drive")


class DriveService:
    def __init__(self, auth):
        self.service = build("drive", "v3", credentials=auth.credentials(), cache_discovery=False)

    def search(self, query: str, page_size: int = 10) -> List[dict]:
        # Recherche par nom (case-insensitive)
        q = f"name contains '{query}' and trashed = false"
        resp = self.service.files().list(
            q=q, pageSize=page_size,
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        ).execute()
        return resp.get("files", [])

    def recent(self, page_size: int = 10) -> List[dict]:
        resp = self.service.files().list(
            orderBy="modifiedTime desc", pageSize=page_size, q="trashed = false",
            fields="files(id, name, mimeType, webViewLink, modifiedTime)",
        ).execute()
        return resp.get("files", [])
