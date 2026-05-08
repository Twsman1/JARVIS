import threading
from jarvis import core
from jarvis.voice.recorder import AudioRecorder
from jarvis.voice.transcriber import Transcriber
from jarvis.voice.wake_word import WakeWordListener
from jarvis.core import _command_active
from jarvis.hud import state

class VoicePipeline:
    def __init__(self, on_command_callback):
        self.on_command_callback = on_command_callback
        self.recorder = AudioRecorder()
        self.transcriber = Transcriber()
        self._processing = False
        self.wake_listener = WakeWordListener(callback=self.on_wake_word)
        core.log.info("Pipeline de voz inicializado")

    def start(self):
        self.wake_listener.start()
        core.log.info("Aguardando wake word...")

    def on_wake_word(self):
        if self._processing:
            core.log.info("Comando já em processamento, ignorando wake word")
            return
        threading.Thread(target=self._handle_command, daemon=True).start()

    def _handle_command(self):
        self._processing = True
        try:
            state.set_state(state.LISTENING, "gravando comando")
            core.speak("Sim, senhor?")
            audio = self.recorder.record()
            if len(audio) == 0:
                core.speak("Não captei nada.")
                return
            text = self.transcriber.transcribe(audio)
            core.log.info(f"Comando transcrito: {text}")
            if text.strip():
                state.add_to_log("user", text)
                self.on_command_callback(text.strip())
            else:
                core.speak("Não entendi, pode repetir?")
        except Exception as e:
            core.log.info(f"Erro no pipeline: {e}")
        finally:
            self._processing = False
            _command_active.clear()