import datetime
import os
import subprocess
import sys
import webbrowser

from jarvis.core import speak, update_status
from jarvis.config import WHISPER_MODEL


def _cmd_hora():
    now = datetime.datetime.now().strftime("%H:%M")
    speak(f"Agora sao {now}")
    update_status("Hora: " + now)


def _cmd_data():
    meses = ["janeiro","fevereiro","marco","abril","maio","junho",
             "julho","agosto","setembro","outubro","novembro","dezembro"]
    d  = datetime.datetime.now()
    ds = f"{d.day} de {meses[d.month-1]} de {d.year}"
    speak(f"Hoje e {ds}")
    update_status("Data: " + ds)


def _cmd_open(url: str, name: str):
    speak(f"Abrindo {name}, senhor.")
    update_status("Abrindo: " + name)
    webbrowser.open(url)


def _cmd_calculator():
    speak("Calculadora ativada.")
    update_status("Calculadora")
    try:
        if sys.platform == "win32":    os.startfile("calc")
        elif sys.platform == "darwin": subprocess.Popen(["open", "-a", "Calculator"])
        else:                          subprocess.Popen(["gnome-calculator"])
    except Exception as e:
        from jarvis.core import log
        log.warning("Calc: %s", e)


def _cmd_standby():
    speak("Entrando em modo de espera. Diga acorde para reativar.")
    update_status("STANDBY")


def _cmd_shutdown():
    from jarvis.hud import renderer
    from jarvis.core import log

    log.info("Comando de desligamento recebido, saindo.")
    speak("Encerrando todos os sistemas. Ate logo, senhor.")
    update_status("DESLIGANDO...")
    # renderer.root is created during init
    renderer.root.after(2500, renderer.root.destroy)


def _cmd_joke():
    import random
    jokes = [
        "Por que o JavaScript foi ao psicologo? Porque tinha problemas com seu escopo.",
        "Qual e o animal mais antigo? A zebra, porque esta em preto e branco.",
        "Por que o livro de matematica estava triste? Tinha muitos problemas.",
    ]
    speak(random.choice(jokes))
    update_status("Piada contada")


def _cmd_version():
    speak(f"JARVIS versao 4.7.1. Motor de voz faster-whisper, modelo {WHISPER_MODEL}, idioma portugues.")
    update_status(f"JARVIS v4.7.1 | Whisper {WHISPER_MODEL} | PT-BR")