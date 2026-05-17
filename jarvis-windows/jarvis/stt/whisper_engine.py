"""Reconnaissance vocale via faster-whisper (CTranslate2) sur CUDA.

Utilise un VAD WebRTC pour détecter le début/fin de parole, puis transcrit
en français avec faster-whisper large-v3 par défaut.
"""
from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Optional

import numpy as np

log = logging.getLogger("jarvis.stt")

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_SAMPLES = int(SAMPLE_RATE * FRAME_MS / 1000)
SILENCE_TIMEOUT_MS = 800
MAX_SEGMENT_SECONDS = 15


class WhisperEngine:
    def __init__(self, cfg):
        self.cfg = cfg
        self.device = cfg.device or "cuda"
        self.compute_type = cfg.compute_type or "float16"
        self.language = cfg.language or "fr"
        self.model_name = cfg.model or "large-v3"
        self.vad_enabled = bool(cfg.vad_filter)
        self.input_device = cfg.input_device
        self._model = None
        self._vad = None
        self._closed = False
        self._load()

    def _load(self):
        try:
            from faster_whisper import WhisperModel

            log.info("Chargement faster-whisper %s sur %s (%s)...",
                     self.model_name, self.device, self.compute_type)
            self._model = WhisperModel(
                self.model_name,
                device=self.device,
                compute_type=self.compute_type,
            )
            if self.vad_enabled:
                import webrtcvad
                self._vad = webrtcvad.Vad(2)
            log.info("STT prêt.")
        except Exception as e:
            log.exception("Échec chargement Whisper : %s", e)
            self._model = None

    def _record_until_silence(self, timeout: float) -> Optional[np.ndarray]:
        """Enregistre depuis le micro jusqu'à détecter ~SILENCE_TIMEOUT_MS de silence."""
        import sounddevice as sd

        q: "queue.Queue[np.ndarray]" = queue.Queue()

        def callback(indata, frames, t, status):
            if status:
                log.debug("Audio status: %s", status)
            q.put(indata.copy())

        speech_frames: list[np.ndarray] = []
        silence_ms = 0
        speech_started = False
        start_time = time.time()

        try:
            with sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
                blocksize=FRAME_SAMPLES,
                device=self.input_device,
                callback=callback,
            ):
                while not self._closed:
                    try:
                        frame = q.get(timeout=0.5)
                    except queue.Empty:
                        if time.time() - start_time > timeout and not speech_started:
                            return None
                        continue

                    pcm = frame.flatten()
                    pcm_bytes = pcm.astype(np.int16).tobytes()

                    is_speech = True
                    if self._vad is not None:
                        try:
                            is_speech = self._vad.is_speech(pcm_bytes, SAMPLE_RATE)
                        except Exception:
                            is_speech = True

                    if is_speech:
                        if not speech_started:
                            log.debug("Parole détectée.")
                        speech_started = True
                        silence_ms = 0
                        speech_frames.append(pcm)
                    elif speech_started:
                        silence_ms += FRAME_MS
                        speech_frames.append(pcm)
                        if silence_ms >= SILENCE_TIMEOUT_MS:
                            break

                    if speech_started and len(speech_frames) * FRAME_MS / 1000 > MAX_SEGMENT_SECONDS:
                        break
                    if not speech_started and time.time() - start_time > timeout:
                        return None
        except Exception as e:
            log.exception("Erreur capture micro : %s", e)
            return None

        if not speech_frames:
            return None
        audio = np.concatenate(speech_frames).astype(np.float32) / 32768.0
        return audio

    def listen(self, timeout: float = 8.0) -> Optional[str]:
        if self._model is None:
            log.warning("Whisper non chargé, STT désactivé.")
            return None

        audio = self._record_until_silence(timeout=timeout)
        if audio is None or len(audio) < SAMPLE_RATE * 0.3:
            return None

        try:
            segments, _info = self._model.transcribe(
                audio,
                language=self.language,
                vad_filter=False,
                beam_size=5,
            )
            text = "".join(seg.text for seg in segments).strip()
            return text or None
        except Exception as e:
            log.exception("Erreur transcription : %s", e)
            return None

    def close(self):
        self._closed = True
