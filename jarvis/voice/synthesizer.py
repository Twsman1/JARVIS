import threading
import io
import sounddevice as sd
import soundfile as sf
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
            # Sintetizar para bytes WAV
            wav_bytes = io.BytesIO()
            self.voice.synthesize(text, wav_bytes)
            wav_bytes.seek(0)
            # Ler com soundfile
            audio, sample_rate = sf.read(wav_bytes, dtype='float32')
            # Reproduzir
            sd.play(audio, samplerate=sample_rate)
            sd.wait()
        except Exception as e:
            core.log.info(f"Erro na síntese: {e}")
        finally:
            state.set_state(state.IDLE)