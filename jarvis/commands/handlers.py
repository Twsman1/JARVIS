import datetime
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

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

def _cmd_open_chrome():
    """Open Google Chrome (or fallback to default browser)."""
    speak("Abrindo Chrome, senhor.")
    update_status("Abrindo: Chrome")
    try:
        if sys.platform == "win32":
            # Try common locations first
            candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            ]
            for p in candidates:
                if os.path.exists(p):
                    subprocess.Popen([p])
                    return
            # If not found, try shell association / PATH
            subprocess.Popen(["chrome"])
            return
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Google Chrome"])
            return
        else:
            subprocess.Popen(["google-chrome"])
            return
    except Exception:
        # fallback to default browser
        try:
            webbrowser.open("https://google.com")
        except Exception:
            pass


def _cmd_open_folder(folder_path: str, name: str):
    """Open a folder in the system file explorer."""
    speak(f"Abrindo pasta {name}, senhor.")
    update_status("Abrindo pasta: " + name)
    try:
        p = Path(folder_path).expanduser()
        if sys.platform == "win32":
            os.startfile(str(p))
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
        else:
            subprocess.Popen(["xdg-open", str(p)])
    except Exception as e:
        from jarvis.core import log
        log.warning("Open folder: %s", e)


def _user_folder(which: str) -> tuple[str, str] | None:
    """Return (path, display_name) for common user folders."""
    home = Path.home()
    key = which.strip().lower()

    mapping = {
        "downloads": (home / "Downloads", "Downloads"),
        "download": (home / "Downloads", "Downloads"),
        "documentos": (home / "Documents", "Documentos"),
        "documento": (home / "Documents", "Documentos"),
        "docs": (home / "Documents", "Documentos"),
        "desktop": (home / "Desktop", "Desktop"),
        "área de trabalho": (home / "Desktop", "Desktop"),
        "area de trabalho": (home / "Desktop", "Desktop"),
        "imagens": (home / "Pictures", "Imagens"),
        "fotos": (home / "Pictures", "Imagens"),
        "pictures": (home / "Pictures", "Imagens"),
        "vídeos": (home / "Videos", "Vídeos"),
        "videos": (home / "Videos", "Vídeos"),
        "músicas": (home / "Music", "Músicas"),
        "musicas": (home / "Music", "Músicas"),
        "home": (home, "Home"),
        "usuario": (home, "Usuário"),
        "usuário": (home, "Usuário"),
    }

    val = mapping.get(key)
    if not val:
        return None
    return (str(val[0]), val[1])


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
    model_label = WHISPER_MODEL or "local"
    speak(f"JARVIS versao 4.7.1. Motor de voz faster-whisper, modelo {model_label}, idioma portugues.")
    update_status(f"JARVIS v4.7.1 | Whisper {model_label} | PT-BR")