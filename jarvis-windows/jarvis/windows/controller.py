"""Contrôleur système Windows 11 : volume, veille, capture, lancement apps."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import psutil

log = logging.getLogger("jarvis.windows")


COMMON_APPS = {
    "bloc-notes": "notepad.exe",
    "bloc notes": "notepad.exe",
    "calculatrice": "calc.exe",
    "calculette": "calc.exe",
    "explorateur": "explorer.exe",
    "explorateur de fichiers": "explorer.exe",
    "navigateur": "start microsoft-edge:",
    "chrome": "chrome.exe",
    "edge": "start microsoft-edge:",
    "firefox": "firefox.exe",
    "spotify": "spotify.exe",
    "vs code": "code.exe",
    "vscode": "code.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "terminal": "wt.exe",
    "powershell": "powershell.exe",
    "paramètres": "start ms-settings:",
    "parametres": "start ms-settings:",
    "panneau de configuration": "control.exe",
}


class WindowsController:
    def __init__(self, cfg):
        from jarvis.config import ROOT
        self.cfg = cfg
        self.shutdown_grace = int(cfg.get("shutdown_grace_seconds", 30))
        self.screenshot_dir = Path(cfg.get("screenshot_dir") or "screenshots")
        if not self.screenshot_dir.is_absolute():
            self.screenshot_dir = ROOT / self.screenshot_dir
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

    # ---------- Time / system ----------
    def current_time_fr(self) -> str:
        now = datetime.now()
        return f"Il est {now.hour} heures {now.minute:02d}."

    def battery_status_fr(self) -> str:
        bat = psutil.sensors_battery()
        if not bat:
            return "Pas de batterie détectée."
        plugged = "branché" if bat.power_plugged else "sur batterie"
        return f"Batterie à {int(bat.percent)} pour cent, {plugged}."

    # ---------- Power ----------
    def lock(self) -> None:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.LockWorkStation()

    def sleep(self) -> None:
        if sys.platform == "win32":
            subprocess.run(["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"])

    def shutdown(self, delay_minutes: int = 0) -> None:
        if sys.platform != "win32":
            return
        secs = max(delay_minutes * 60, 0)
        subprocess.run(["shutdown", "/s", "/t", str(secs)])

    def cancel_shutdown(self) -> None:
        if sys.platform == "win32":
            subprocess.run(["shutdown", "/a"])

    # ---------- Volume (pycaw) ----------
    def _get_volume_interface(self):
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))

    def set_volume(self, percent: int) -> None:
        percent = max(0, min(100, percent))
        try:
            vol = self._get_volume_interface()
            vol.SetMasterVolumeLevelScalar(percent / 100.0, None)
        except Exception as e:
            log.exception("set_volume : %s", e)

    def mute(self) -> None:
        try:
            self._get_volume_interface().SetMute(1, None)
        except Exception as e:
            log.exception("mute : %s", e)

    def volume_up(self, step: int = 10) -> None:
        try:
            vol = self._get_volume_interface()
            cur = vol.GetMasterVolumeLevelScalar()
            vol.SetMasterVolumeLevelScalar(min(1.0, cur + step / 100.0), None)
        except Exception as e:
            log.exception("volume_up : %s", e)

    def volume_down(self, step: int = 10) -> None:
        try:
            vol = self._get_volume_interface()
            cur = vol.GetMasterVolumeLevelScalar()
            vol.SetMasterVolumeLevelScalar(max(0.0, cur - step / 100.0), None)
        except Exception as e:
            log.exception("volume_down : %s", e)

    # ---------- Screenshot ----------
    def screenshot(self) -> str:
        import pyautogui
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.screenshot_dir / f"capture_{ts}.png"
        img = pyautogui.screenshot()
        img.save(path)
        return str(path)

    # ---------- Launch apps ----------
    def open_app(self, name: str) -> bool:
        name_l = name.lower().strip()
        target = COMMON_APPS.get(name_l)
        if not target:
            target = name  # tentative directe
        try:
            if target.startswith("start "):
                os.system(target)
            else:
                subprocess.Popen(target, shell=True)
            return True
        except Exception as e:
            log.exception("open_app(%s) : %s", name, e)
            return False
