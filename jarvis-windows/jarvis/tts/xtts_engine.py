"""Synthèse vocale Coqui XTTS-v2 sur GPU CUDA (RTX 3070)."""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Optional

log = logging.getLogger("jarvis.tts")


class XTTSEngine:
    """Wrapper autour de Coqui TTS XTTS-v2 avec lecture audio synchrone.

    Le modèle XTTS-v2 nécessite :
        pip install TTS torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    """

    MODEL_NAME = "tts_models/multilingual/multi-dataset/xtts_v2"

    def __init__(self, cfg):
        self.cfg = cfg
        self.device = cfg.device or "cuda"
        self.language = cfg.language or "fr"
        self.speed = cfg.get("speed", 1.0)
        self.speaker_wav = self._resolve_speaker_wav(cfg.speaker_wav)
        self._lock = threading.Lock()
        self._tts = None
        self._load()

    def _resolve_speaker_wav(self, raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        p = Path(raw)
        if not p.is_absolute():
            from jarvis.config import ROOT
            p = ROOT / raw
        return str(p) if p.exists() else None

    def _load(self) -> None:
        try:
            from TTS.api import TTS  # import paresseux
            import torch

            if self.device == "cuda" and not torch.cuda.is_available():
                log.warning("CUDA indisponible, bascule en CPU (synthèse lente).")
                self.device = "cpu"

            log.info("Chargement XTTS-v2 sur %s (1ʳᵉ exécution = ~2 Go téléchargés)...", self.device)
            self._tts = TTS(self.MODEL_NAME, progress_bar=False).to(self.device)
            if self.cfg.precision == "float16" and self.device == "cuda":
                try:
                    self._tts.synthesizer.tts_model = self._tts.synthesizer.tts_model.half()
                except Exception:
                    log.debug("FP16 non appliqué (modèle ne supporte pas .half()).")
            log.info("XTTS-v2 prêt.")
        except Exception as e:
            log.exception("Échec chargement XTTS-v2 : %s", e)
            self._tts = None

    def speak(self, text: str) -> None:
        if not text:
            return
        if self._tts is None:
            log.warning("XTTS non chargé, fallback impression console.")
            print(f"[Jarvis] {text}")
            return

        with self._lock:
            try:
                import numpy as np
                import sounddevice as sd

                wav = self._tts.tts(
                    text=text,
                    language=self.language,
                    speaker_wav=self.speaker_wav,
                    speed=self.speed,
                )
                wav_np = np.array(wav, dtype="float32")
                sr = self._tts.synthesizer.output_sample_rate
                sd.play(wav_np, samplerate=sr, blocking=True)
            except Exception as e:
                log.exception("Erreur synthèse vocale : %s", e)
                print(f"[Jarvis] {text}")
