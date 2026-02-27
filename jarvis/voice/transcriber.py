import threading
import tempfile
import wave
import os

import numpy as np
from faster_whisper import WhisperModel

from jarvis.config import WHISPER_MODEL, WHISPER_LANG, SAMPLE_RATE
from jarvis.core import log, update_status


class WhisperTranscriber:
    def __init__(self):
        self._model = None
        self._ready = threading.Event()
        threading.Thread(target=self._load, daemon=True, name="Whisper-load").start()

    def _load(self):
        try:
            update_status("Carregando Whisper (" + WHISPER_MODEL + ")...")
            self._model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
            self._ready.set()
            update_status("Whisper pronto — qualidade maxima PT-BR")
            log.info("faster-whisper modelo '%s' carregado.", WHISPER_MODEL)
        except Exception as e:
            log.error("Falha ao carregar Whisper: %s", e)
            update_status("ERRO Whisper: " + str(e))

    def wait_ready(self, timeout=60) -> bool:
        return self._ready.wait(timeout)

    @property
    def ready(self) -> bool:
        return self._ready.is_set()

    def transcribe(self, pcm_int16: np.ndarray) -> str:
        if not self.ready:
            return ""
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                tmp_path = f.name
            with wave.open(tmp_path, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(pcm_int16.tobytes())
            segments, info = self._model.transcribe(
                tmp_path,
                language=WHISPER_LANG,
                beam_size=4,
                best_of=3,
                temperature=0.0,
                condition_on_previous_text=False,
                vad_filter=True,
                vad_parameters=dict(threshold=0.4, min_silence_duration_ms=300),
            )
            text = " ".join(s.text.strip() for s in segments).strip().lower()
            log.info("Whisper: '%s' (lang=%s, prob=%.2f)",
                     text, info.language, info.language_probability)
            return text
        except Exception as e:
            log.error("Transcricao: %s", e)
            return ""
        finally:
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass


whisper_asr = WhisperTranscriber()
