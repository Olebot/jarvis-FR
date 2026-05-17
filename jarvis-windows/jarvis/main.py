"""Point d'entrée Jarvis."""
from __future__ import annotations

import logging
import os
import signal
import sys
import threading
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from jarvis.config import CONFIG, ROOT
from jarvis.core.assistant import Assistant
from jarvis.ui.tray import run_tray

console = Console()


def setup_logging() -> None:
    level = os.environ.get("JARVIS_LOG_LEVEL", "INFO").upper()
    log_dir = ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(console=console, rich_tracebacks=True, show_path=False),
            logging.FileHandler(log_dir / "jarvis.log", encoding="utf-8"),
        ],
    )


def main() -> int:
    setup_logging()
    log = logging.getLogger("jarvis")
    log.info("Démarrage Jarvis FR v1.0.0")
    log.info("Racine : %s", ROOT)

    assistant = Assistant(CONFIG)

    # Gestion Ctrl+C
    def _on_signal(signum, frame):
        log.info("Arrêt demandé (signal %s)…", signum)
        assistant.stop()

    signal.signal(signal.SIGINT, _on_signal)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _on_signal)

    # Tray dans un thread si activé
    if CONFIG.ui.get("show_tray_icon", True):
        threading.Thread(target=run_tray, args=(assistant,), daemon=True).start()

    try:
        assistant.run()
    except KeyboardInterrupt:
        pass
    finally:
        assistant.stop()

    log.info("Jarvis terminé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
