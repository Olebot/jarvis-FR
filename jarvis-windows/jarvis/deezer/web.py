"""Contrôle de Deezer Web (deezer.com) via Playwright."""
from __future__ import annotations

import logging
import threading
from typing import Optional

log = logging.getLogger("jarvis.deezer.web")


class DeezerWeb:
    def __init__(self, cfg):
        self.cfg = cfg
        self.url = cfg.web_url or "https://www.deezer.com"
        self.headless = bool(cfg.web_headless)
        self._pw = None
        self._browser = None
        self._page = None
        self._lock = threading.Lock()

    def _ensure_browser(self):
        if self._page is not None:
            return
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch_persistent_context(
                user_data_dir=self._user_data_dir(),
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            self._page = self._browser.new_page()
        except Exception as e:
            log.exception("Playwright KO : %s — installez avec : playwright install chromium", e)

    def _user_data_dir(self) -> str:
        from jarvis.config import ROOT
        d = ROOT / "config" / "deezer_chromium"
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    def is_running(self) -> bool:
        return self._page is not None

    def launch(self):
        with self._lock:
            self._ensure_browser()
            if self._page:
                self._page.goto(self.url)

    def close(self):
        with self._lock:
            try:
                if self._browser:
                    self._browser.close()
            finally:
                self._browser = None
                self._page = None
                if self._pw:
                    self._pw.stop()
                    self._pw = None

    # ---- Contrôles ----
    def _click_play_pause(self):
        with self._lock:
            self._ensure_browser()
            if not self._page:
                return
            try:
                btn = self._page.locator('button[data-testid="play-pause-control"]')
                btn.first.click(timeout=5000)
            except Exception:
                # Fallback raccourci clavier Deezer Web
                try:
                    self._page.keyboard.press("Space")
                except Exception as e:
                    log.exception("Play/Pause Deezer Web : %s", e)

    def play(self):       self._click_play_pause()
    def pause(self):      self._click_play_pause()

    def next_track(self):
        with self._lock:
            self._ensure_browser()
            try:
                self._page.locator('button[data-testid="next-control"]').first.click(timeout=5000)
            except Exception:
                try:
                    self._page.keyboard.press("Control+ArrowRight")
                except Exception as e:
                    log.exception("Next Deezer Web : %s", e)

    def prev_track(self):
        with self._lock:
            self._ensure_browser()
            try:
                self._page.locator('button[data-testid="prev-control"]').first.click(timeout=5000)
            except Exception:
                try:
                    self._page.keyboard.press("Control+ArrowLeft")
                except Exception as e:
                    log.exception("Prev Deezer Web : %s", e)

    def play_playlist(self, name: str) -> Optional[bool]:
        with self._lock:
            self._ensure_browser()
            if not self._page:
                return False
            try:
                self._page.goto(f"{self.url}/search/{name}/playlist")
                self._page.wait_for_load_state("networkidle", timeout=8000)
                first = self._page.locator('a[href*="/playlist/"]').first
                first.click()
                self._page.wait_for_timeout(2000)
                self._page.locator('button[data-testid="play"]').first.click()
                return True
            except Exception as e:
                log.exception("play_playlist : %s", e)
                return False
