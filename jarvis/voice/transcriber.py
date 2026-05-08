from faster_whisper import WhisperModel
import numpy as np
from jarvis import core

class Transcriber:
    def __init__(self, model_size="small"):
        core.log(f"Carregando modelo Whisper {model_size}...")
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        core.log("Modelo Whisper pronto.")

    def transcribe(self, audio: np.ndarray) -> str:
        try:
            # Converter para float32 normalizado
            audio_float = audio.astype(np.float32) / 32768.0
            segments, info = self.model.transcribe(
                audio_float,
                language="pt",
                beam_size=5,
                vad_filter=True
            )
            text = "".join(segment.text for segment in segments).strip()
            core.log(f"Transcrição concluída: '{text}'")
            return text
        except Exception as e:
            core.log(f"Erro na transcrição: {e}")
            return ""
