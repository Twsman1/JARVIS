import threading
import sounddevice as sd
from pathlib import Path
from piper import PiperVoice
from jarvis import core
from jarvis.hud import state

MODEL_PATH = Path("jarvis/data/voices/pt_BR-faber-medium.onnx")
CONFIG_PATH = Path("jarvis/data/voices/pt_BR-faber-medium.onnx.json")

class Synthesizer:
    def __init__(self):
        if not MODEL_PATH.exists() or not CONFIG_PATH.exists():
            error_msg = f"Arquivos de voz não encontrados: {MODEL_PATH} ou {CONFIG_PATH}"
            core.log.info(error_msg)
            raise FileNotFoundError(error_msg)
        self.voice = PiperVoice.load(str(MODEL_PATH), config_path=str(CONFIG_PATH))
        core.log.info("Sintetizador de voz pronto (Piper PT-BR)")

    def start(self):
        self.thread = threading.Thread(target=self.speak_worker, daemon=True)
        self.thread.start()

    def speak_worker(self):
        while True:
            try:
                item = core._tts_queue.get()
                if item is None:
                    core.log.info("Encerrando sintetizador de voz")
                    break
                if isinstance(item, str):
                    self._synthesize_and_play(item)
            except Exception as e:
                core.log.info(f"Erro no sintetizador: {e}")

    def _synthesize_and_play(self, text: str):
        try:
            state.set_state(state.SPEAKING, text[:30])
            # Synthesize to PCM via Piper chunks (no WAV container)
            chunks = list(self.voice.synthesize(text))
            if not chunks:
                return

            sample_rate = chunks[0].sample_rate or getattr(self.voice.config, "sample_rate", 22050)
            audio = []
            for ch in chunks:
                # Use float32 array for sounddevice
                a = ch.audio_float_array
                if a is None:
                    # Fallback to int16 -> float32
                    ai16 = ch.audio_int16_array
                    if ai16 is None:
                        continue
                    a = ai16.astype("float32") / 32768.0
                audio.append(a)

            if not audio:
                return

            audio_f = __import__("numpy").concatenate(audio)
            sd.play(audio_f, samplerate=int(sample_rate))
            sd.wait()
        except Exception as e:
            core.log.info(f"Erro na síntese: {e}")
        finally:
            state.set_state(state.IDLE)