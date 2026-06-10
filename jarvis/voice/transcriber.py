import os
from pathlib import Path

from faster_whisper import WhisperModel
import numpy as np
from jarvis import core
from jarvis.config import WHISPER_MODEL, WHISPER_LANG

class Transcriber:
    def __init__(self, model_size: str | None = None):
        model_size = model_size or WHISPER_MODEL

        # If using a local directory, force offline behavior.
        # (Prevents any accidental HF hub calls if some file is missing.)
        if model_size is None:
            core.log.error(
                "Whisper local não configurado. Defina JARVIS_WHISPER_DIR para uma pasta com model.bin."
            )
            self.model = None
            self.ready = False
            return

        p = Path(model_size)
        if p.exists() and p.is_dir():
            # Only treat it as a valid faster-whisper model dir if model.bin exists
            if (p / "model.bin").is_file():
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                core.log.info("Whisper: usando modelo local em '%s' (modo offline)", str(p))
            else:
                core.log.error(
                    "Whisper: pasta local '%s' existe, mas faltou 'model.bin'. "
                    "Offline ASR está desabilitado até que o modelo seja instalado.",
                    str(p),
                )
                self.model = None
                self.ready = False
                return
        else:
            core.log.error(
                "Whisper: diretório local '%s' não existe. Offline ASR está desabilitado.",
                model_size,
            )
            self.model = None
            self.ready = False
            return

        core.log.info("Carregando modelo Whisper %s...", model_size)
        # Passing a local directory path makes faster-whisper load from disk.
        self.model = WhisperModel(str(model_size), device="cpu", compute_type="int8")
        core.log.info("Modelo Whisper pronto.")
        self.ready = True

    def wait_ready(self, timeout=30):
        # Since loading is synchronous, it's always ready
        pass

    def transcribe(self, audio: np.ndarray) -> str:
        if self.model is None:
            core.log.error("Transcrição indisponível: Whisper offline não foi carregado.")
            return ""
        try:
            # Converter para float32 normalizado
            audio_float = audio.astype(np.float32) / 32768.0
            segments, info = self.model.transcribe(
                audio_float,
                language=WHISPER_LANG,
                beam_size=5,
                vad_filter=True
            )
            text = "".join(segment.text for segment in segments).strip()
            core.log.info(f"Transcrição concluída: '{text}'")
            return text
        except Exception as e:
            core.log.info(f"Erro na transcrição: {e}")
            return ""

whisper_asr = Transcriber()
