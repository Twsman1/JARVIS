import pyperclip
from jarvis import core

def read_clipboard() -> str:
    core.log.info("Lendo clipboard")
    try:
        content = pyperclip.paste()
        if content:
            return content[:1000] if len(content) > 1000 else content
        else:
            return "Clipboard está vazio."
    except Exception as e:
        core.log.info(f"Erro ao ler clipboard: {e}")
        return f"Erro ao ler clipboard: {str(e)}"

def write_clipboard(text: str) -> str:
    core.log.info(f"Escrevendo no clipboard: {len(text)} caracteres")
    try:
        pyperclip.copy(text)
        return f"Texto copiado para o clipboard ({len(text)} caracteres)."
    except Exception as e:
        core.log.info(f"Erro ao escrever clipboard: {e}")
        return f"Erro ao escrever no clipboard: {str(e)}"