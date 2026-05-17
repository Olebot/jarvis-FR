"""Chargement de la configuration YAML + .env."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _resolve_root() -> Path:
    """Racine de l'installation = JARVIS_HOME ou parent de ce fichier."""
    env_home = os.environ.get("JARVIS_HOME")
    if env_home:
        return Path(env_home)
    return Path(__file__).resolve().parent.parent


ROOT = _resolve_root()
CONFIG_DIR = ROOT / "config"
CONFIG_FILE = CONFIG_DIR / "config.yaml"
ENV_FILE = CONFIG_DIR / ".env"

if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


class Config:
    """Accès dot-notation au config.yaml."""

    def __init__(self, data: dict[str, Any]):
        self._data = data

    def __getattr__(self, key: str) -> Any:
        value = self._data.get(key)
        if isinstance(value, dict):
            return Config(value)
        return value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, Any]:
        return self._data


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        example = CONFIG_DIR / "config.example.yaml"
        if example.exists():
            CONFIG_FILE.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            raise FileNotFoundError(f"Aucun config trouvé : {CONFIG_FILE}")
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return Config(data)


CONFIG = load_config()
