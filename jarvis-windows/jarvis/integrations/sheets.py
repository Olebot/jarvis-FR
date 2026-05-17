"""Google Sheets."""
from __future__ import annotations

import logging
from typing import List, Optional

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.sheets")


class SheetsService:
    def __init__(self, auth):
        self.sheets = build("sheets", "v4", credentials=auth.credentials(), cache_discovery=False)
        self.drive = build("drive", "v3", credentials=auth.credentials(), cache_discovery=False)

    def create(self, title: str) -> str:
        ss = self.sheets.spreadsheets().create(body={"properties": {"title": title}}).execute()
        return ss["spreadsheetUrl"]

    def last_opened(self) -> Optional[dict]:
        r = self.drive.files().list(
            q="mimeType='application/vnd.google-apps.spreadsheet' and trashed = false",
            orderBy="viewedByMeTime desc", pageSize=1,
            fields="files(id, name, webViewLink)",
        ).execute()
        files = r.get("files", [])
        return files[0] if files else None

    def append_row(self, spreadsheet_id: str, sheet_name: str, row: List[str]) -> None:
        self.sheets.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"{sheet_name}!A1",
            valueInputOption="USER_ENTERED",
            body={"values": [row]},
        ).execute()
