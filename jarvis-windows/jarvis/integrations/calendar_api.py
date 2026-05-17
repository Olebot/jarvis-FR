"""Google Calendar."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.calendar")


class CalendarService:
    def __init__(self, auth):
        self.service = build("calendar", "v3", credentials=auth.credentials(), cache_discovery=False)

    def today(self) -> List[dict]:
        now = datetime.now(timezone.utc)
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self._list(start, end)

    def upcoming(self, days: int = 7) -> List[dict]:
        now = datetime.now(timezone.utc)
        return self._list(now, now + timedelta(days=days))

    def _list(self, start: datetime, end: datetime) -> List[dict]:
        events = self.service.events().list(
            calendarId="primary",
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        out = []
        for e in events.get("items", []):
            s = e["start"].get("dateTime", e["start"].get("date"))
            out.append({
                "id": e["id"],
                "summary": e.get("summary", "(sans titre)"),
                "start": s,
            })
        return out

    def quick_add(self, text: str) -> str:
        ev = self.service.events().quickAdd(calendarId="primary", text=text).execute()
        return ev.get("id", "")
