"""Icône dans la zone de notification Windows."""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger("jarvis.ui.tray")


def _make_icon():
    """Petite icône PIL générée (sans dépendance à un .ico externe)."""
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (64, 64), color=(20, 22, 30))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=(118, 224, 199))
    d.text((22, 20), "J", fill=(20, 22, 30))
    return img


def run_tray(assistant) -> None:
    try:
        import pystray
        from pystray import MenuItem as Item, Menu

        def on_quit(icon, item):
            assistant.stop()
            icon.stop()

        def on_speak_hello(icon, item):
            assistant.speak("Bonjour, je suis là.")

        icon = pystray.Icon(
            "jarvis",
            _make_icon(),
            "Jarvis FR",
            menu=Menu(
                Item("Bonjour", on_speak_hello),
                Item("Quitter", on_quit),
            ),
        )
        icon.run()
    except Exception as e:
        log.exception("Tray indisponible : %s", e)
