"""Entry point for the JARVIS HUD application."""

from jarvis.core import log, _shutdown, _tts_queue, speak, add_history
import jarvis.hud.renderer as renderer
from jarvis.voice.synthesizer import Synthesizer
from jarvis.voice.pipeline import VoicePipeline
from jarvis.brain.brain import Brain
from jarvis.commands.registry import execute_command
from jarvis.hud import state


def _on_close():
    log.info("Janela fechada, iniciando desligamento.")
    _shutdown.set()
    _tts_queue.put(None)
    renderer.root.destroy()


def main():
    root, canvas = renderer.init_gui()
    renderer.draw_hud()
    renderer._draw_loading_overlay()

    # Inicializar Synthesizer
    synthesizer = Synthesizer()
    synthesizer.start()

    # Inicializar o cérebro
    brain = Brain(model="llama3")

    # Substituir on_command pelo Brain
    def on_command(text: str):
        log.info("Processando comando: %s", text)
        add_history(text)

        # 1) First, try deterministic mapped commands (offline, no LLM needed)
        if execute_command(text, speak_on_fail=False):
            return

        # 2) Otherwise fall back to Brain (LLM/tools)
        state.add_to_log("user", text)
        response = brain.think(text)
        if response:
            state.add_to_log("jarvis", response)
            speak(response)

    # Substituir WakeWordListener por VoicePipeline
    pipeline = VoicePipeline(on_command_callback=on_command)
    pipeline.start()

    # announce that everything is ready (helps verify audio output)
    speak("JARVIS pronto, senhor.")

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
