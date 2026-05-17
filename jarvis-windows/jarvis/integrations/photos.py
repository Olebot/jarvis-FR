"""Google Photos (Library API)."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

from googleapiclient.discovery import build

log = logging.getLogger("jarvis.google.photos")


class PhotosService:
    """Note : depuis 2025, l'API Library Google Photos limite l'accès aux
    médias créés/uploadés par l'application. Pour explorer toute votre
    bibliothèque, créez les médias via Jarvis ou utilisez Drive comme
    alternative."""

    API_NAME = "photoslibrary"
    API_VERSION = "v1"
    DISCOVERY = "https://photoslibrary.googleapis.com/$discovery/rest?version=v1"

    def __init__(self, auth):
        self.service = build(
            self.API_NAME, self.API_VERSION,
            credentials=auth.credentials(),
            discoveryServiceUrl=self.DISCOVERY,
            static_discovery=False,
            cache_discovery=False,
        )

    def list_recent(self, days: int = 7) -> List[dict]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        body = {
            "filters": {
                "dateFilter": {
                    "ranges": [{
                        "startDate": {"year": start.year, "month": start.month, "day": start.day},
                        "endDate":   {"year": end.year,   "month": end.month,   "day": end.day},
                    }]
                }
            },
            "pageSize": 50,
        }
        r = self.service.mediaItems().search(body=body).execute()
        return r.get("mediaItems", [])

    def recent_count(self, days: int = 7) -> int:
        return len(self.list_recent(days=days))
