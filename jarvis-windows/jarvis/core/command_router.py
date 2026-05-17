"""Routeur de commandes vocales en français.

Détecte les intents simples (système Windows, Deezer, Google) avec des
expressions régulières et délègue à l'intégration correspondante.
Si aucun intent ne correspond, retourne (handled=False, None) → l'assistant
fera appel au LLM en mode conversation libre.
"""
from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

from jarvis.windows.controller import WindowsController
from jarvis.deezer.desktop import DeezerDesktop
from jarvis.deezer.web import DeezerWeb
from jarvis.integrations.google_auth import GoogleAuth
from jarvis.integrations.gmail import GmailService
from jarvis.integrations.drive import DriveService
from jarvis.integrations.calendar_api import CalendarService
from jarvis.integrations.docs import DocsService
from jarvis.integrations.sheets import SheetsService
from jarvis.integrations.photos import PhotosService

log = logging.getLogger("jarvis.commands")


class CommandRouter:
    def __init__(self, cfg, llm=None):
        self.cfg = cfg
        self.llm = llm
        self.win = WindowsController(cfg.windows)
        self.deezer_desktop = DeezerDesktop(cfg.deezer)
        self.deezer_web = DeezerWeb(cfg.deezer)
        self._deezer_target = (cfg.deezer.default_target or "ask").lower()
        # Google : init paresseuse pour ne pas bloquer si client_secret manquant
        self._google: Optional[GoogleAuth] = None
        self._gmail = self._drive = self._cal = self._docs = self._sheets = self._photos = None

    # ---------- Google lazy ----------
    def _ensure_google(self) -> bool:
        if self._google is not None:
            return True
        try:
            self._google = GoogleAuth(self.cfg.google)
            self._google.ensure_credentials()
            self._gmail = GmailService(self._google)
            self._drive = DriveService(self._google)
            self._cal = CalendarService(self._google)
            self._docs = DocsService(self._google)
            self._sheets = SheetsService(self._google)
            self._photos = PhotosService(self._google)
            return True
        except Exception as e:
            log.error("Google indisponible : %s", e)
            return False

    # ---------- Main router ----------
    def route(self, text: str) -> Tuple[bool, Optional[str]]:
        t = text.lower().strip()

        # ============ DEEZER : choix de cible ============
        if re.search(r"\b(lance|ouvre|démarre|demarre).*deezer.*\b(bureau|application|appli)\b", t):
            self._deezer_target = "desktop"
            self.deezer_desktop.launch()
            return True, "J'ouvre Deezer sur le bureau."
        if re.search(r"\b(ouvre|lance).*deezer.*\b(navigateur|web|chrome|edge)\b", t):
            self._deezer_target = "web"
            self.deezer_web.launch()
            return True, "J'ouvre Deezer dans le navigateur."
        if "deezer" in t and "ferme" in t:
            self.deezer_desktop.close()
            self.deezer_web.close()
            return True, "Deezer fermé."

        # Contrôles lecture Deezer
        if re.search(r"\b(joue|reprends|play|lecture)\b", t) and "deezer" not in t:
            self._deezer_play()
            return True, "Lecture."
        if re.search(r"\b(pause|stop|arrête|arrete)\b.*\b(musique|deezer|lecture)?", t):
            self._deezer_pause()
            return True, "Pause."
        if re.search(r"\b(piste|chanson|titre).*(suivante|après|apres)\b|\bsuivant\b", t):
            self._deezer_next()
            return True, "Piste suivante."
        if re.search(r"\b(piste|chanson|titre).*(précédente|precedente|d'avant)\b|\bprécédent\b|\bprecedent\b", t):
            self._deezer_prev()
            return True, "Piste précédente."
        m = re.search(r"joue (la )?playlist (.+)", t)
        if m:
            playlist = m.group(2).strip()
            self.deezer_web.play_playlist(playlist)
            return True, f"Je lance la playlist {playlist} sur Deezer Web."

        # ============ WINDOWS 11 ============
        if re.search(r"quelle heure", t):
            return True, self.win.current_time_fr()
        if re.search(r"(niveau|état|etat).*batterie", t):
            return True, self.win.battery_status_fr()
        if re.search(r"capture.*(écran|ecran)|screenshot", t):
            path = self.win.screenshot()
            return True, f"Capture enregistrée dans {path}."
        if re.search(r"verrouille.*ordinateur|lock", t):
            self.win.lock()
            return True, "Ordinateur verrouillé."
        if re.search(r"mets.*veille|sleep", t):
            self.win.sleep()
            return True, "Mise en veille."
        m = re.search(r"éteins|eteins.*ordinateur(?:.*?(\d+).*minute)?", t)
        if m:
            mins = int(m.group(1)) if m.group(1) else 0
            self.win.shutdown(delay_minutes=mins)
            return True, f"Extinction dans {mins} minute(s)." if mins else "Extinction immédiate."
        m = re.search(r"\b(volume).*?(\d{1,3})", t)
        if m:
            vol = int(m.group(2))
            self.win.set_volume(vol)
            return True, f"Volume réglé à {vol} pour cent."
        if "coupe le son" in t or "muet" in t:
            self.win.mute()
            return True, "Son coupé."
        if "augmente le volume" in t:
            self.win.volume_up()
            return True, "Volume augmenté."
        if "baisse le volume" in t or "diminue le volume" in t:
            self.win.volume_down()
            return True, "Volume baissé."
        m = re.search(r"\bouvre (.+)", t)
        if m and "deezer" not in m.group(1) and "mail" not in m.group(1):
            app = m.group(1).strip().rstrip(".!? ")
            ok = self.win.open_app(app)
            return True, f"J'ouvre {app}." if ok else f"Je n'ai pas trouvé {app}."

        # ============ GOOGLE ============
        if re.search(r"(lis|montre|affiche|liste).*(mail|mails|e-?mail|courriel)", t):
            if not self._ensure_google():
                return True, "Google n'est pas configuré."
            mails = self._gmail.list_recent(max_results=5)
            if not mails:
                return True, "Aucun message récent."
            summary = " ; ".join([f"{m['from']} : {m['subject']}" for m in mails])
            return True, f"Vos 5 derniers e-mails : {summary}"

        m = re.search(r"envoie.*mail.*?([\w\.\-]+@[\w\.\-]+).*?[:,]\s*(.+)", t)
        if m and self._ensure_google():
            to, body = m.group(1), m.group(2)
            self._gmail.send(to=to, subject="Message de Jarvis", body=body)
            return True, f"E-mail envoyé à {to}."

        if re.search(r"(rendez-vous|rendezvous|réunion|reunion|agenda|calendrier).*aujourd", t):
            if not self._ensure_google():
                return True, "Google n'est pas configuré."
            events = self._cal.today()
            if not events:
                return True, "Vous n'avez rien aujourd'hui."
            return True, " ; ".join([f"{e['start']} {e['summary']}" for e in events])

        m = re.search(r"ajoute.*(réunion|reunion|rdv|rendez-vous).*(demain|aujourd|le \d).*?(\d{1,2})h(\d{1,2})?[:,]?\s*(.+)?", t)
        if m and self._ensure_google():
            self._cal.quick_add(text)
            return True, "Événement ajouté à votre calendrier."

        m = re.search(r"cherche.*(drive|google drive).*?(?:le |la |un |une )?(?:document |fichier )?(.+)", t)
        if m and self._ensure_google():
            q = m.group(2).strip()
            files = self._drive.search(q)
            if not files:
                return True, "Aucun résultat dans Drive."
            return True, "J'ai trouvé : " + ", ".join([f["name"] for f in files[:5]])

        m = re.search(r"cr(é|e)e.*(google )?doc.*intitul(é|e)?\s*(.+)", t)
        if m and self._ensure_google():
            title = m.group(4).strip()
            self._docs.create(title)
            return True, f"Document créé : {title}."

        if re.search(r"ouvre.*(dernière|derniere).*feuille.*calcul", t):
            if not self._ensure_google():
                return True, "Google n'est pas configuré."
            sheet = self._sheets.last_opened()
            return True, f"J'ouvre {sheet['name']}." if sheet else "Aucune feuille trouvée."

        if re.search(r"(montre|affiche|photos).*(week-end|weekend|hier|semaine)", t):
            if not self._ensure_google():
                return True, "Google Photos n'est pas configuré."
            count = self._photos.recent_count(days=3)
            return True, f"Vous avez {count} photos récentes."

        # Pas d'intent connu → conversation libre via LLM
        return False, None

    # ---------- Helpers Deezer ----------
    def _deezer_target_resolved(self) -> str:
        if self._deezer_target == "ask":
            # Par défaut on essaie l'app desktop si Deezer.exe lancé, sinon web
            if self.deezer_desktop.is_running():
                return "desktop"
            if self.deezer_web.is_running():
                return "web"
            return "desktop"
        return self._deezer_target

    def _deezer_play(self):
        tgt = self._deezer_target_resolved()
        (self.deezer_desktop if tgt == "desktop" else self.deezer_web).play()

    def _deezer_pause(self):
        tgt = self._deezer_target_resolved()
        (self.deezer_desktop if tgt == "desktop" else self.deezer_web).pause()

    def _deezer_next(self):
        tgt = self._deezer_target_resolved()
        (self.deezer_desktop if tgt == "desktop" else self.deezer_web).next_track()

    def _deezer_prev(self):
        tgt = self._deezer_target_resolved()
        (self.deezer_desktop if tgt == "desktop" else self.deezer_web).prev_track()
