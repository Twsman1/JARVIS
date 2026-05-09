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
        p = Path(model_size)
        if p.exists() and p.is_dir():
            # Only treat it as a valid faster-whisper model dir if model.bin exists
            if (p / "model.bin").is_file():
                os.environ.setdefault("HF_HUB_OFFLINE", "1")
                os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
                core.log.info("Whisper: usando modelo local em '%s' (modo offline)", str(p))
            else:
                core.log.warning(
                    "Whisper: pasta local '%s' existe, mas faltou 'model.bin'. "
                    "Baixe o modelo para essa pasta, ou remova a pasta para usar o modelo nomeado.",
                    str(p),
                )
                model_size = "small"
        else:
            core.log.info("Whisper: usando modelo nomeado '%s' (pode acessar internet se não estiver em cache)", model_size)

        core.log.info("Carregando modelo Whisper %s...", model_size)
        # Passing a local directory path makes faster-whisper load from disk.
        self.model = WhisperModel(str(model_size), device="cpu", compute_type="int8")
        core.log.info("Modelo Whisper pronto.")
        self.ready = True

    def wait_ready(self, timeout=30):
        # Since loading is synchronous, it's always ready
        pass

    def transcribe(self, audio: np.ndarray) -> str:
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
