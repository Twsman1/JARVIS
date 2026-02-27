"""Entry point for the JARVIS HUD application."""

from jarvis.core import log, _shutdown, _tts_queue, speak
import jarvis.hud.renderer as renderer
from jarvis.voice.wake_word import WakeWordListener


def _on_close():
    log.info("Janela fechada, iniciando desligamento.")
    _shutdown.set()
    _tts_queue.put(None)
    renderer.root.destroy()


def main():
    root, canvas = renderer.init_gui()
    renderer.draw_hud()
    renderer._draw_loading_overlay()

    listener = WakeWordListener()
    listener.start()

    # announce that everything is ready (helps verify audio output)
    speak("JARVIS pronto, senhor.")

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
