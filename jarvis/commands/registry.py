import re

from .handlers import (
    _cmd_hora,
    _cmd_data,
    _cmd_open,
    _cmd_open_chrome,
    _cmd_open_folder,
    _user_folder,
    _cmd_calculator,
    _cmd_standby,
    _cmd_shutdown,
    _cmd_joke,
    _cmd_version,
)

COMMAND_MAP = {
    r"\bhoras?\b":                   lambda _: _cmd_hora(),
    r"\bdata\b|\bdia\b":             lambda _: _cmd_data(),
    # keep specific patterns before generic ones (e.g. "google chrome" before "google")
    r"\bchrome\b|\bgoogle chrome\b":  lambda _: _cmd_open_chrome(),
    r"\bgoogle\b":                   lambda _: _cmd_open("https://google.com",  "Google"),
    r"\byoutube\b":                  lambda _: _cmd_open("https://youtube.com", "YouTube"),
    r"\bgithub\b":                   lambda _: _cmd_open("https://github.com",  "GitHub"),
    r"\bclima\b|\btempo\b":          lambda _: _cmd_open("https://weather.com", "previsao do tempo"),
    r"\bnoticias?\b|\bnews\b":        lambda _: _cmd_open("https://news.google.com/topstories?hl=pt-BR", "noticias"),
    r"\bcalculadora\b":              lambda _: _cmd_calculator(),
    r"\bparar?\b|\bstandby\b":       lambda _: _cmd_standby(),
    r"\bdesligar\b|\bencerrar\b|\bsair\b": lambda _: _cmd_shutdown(),
    r"\bpiada\b|\bbrincadeira\b":    lambda _: _cmd_joke(),
    r"\bversao\b|\bversão\b|\bsistema\b": lambda _: _cmd_version(),
}


def _try_folder(cmd: str) -> bool:
    """
    Folder open patterns like:
    - "abrir downloads"
    - "abrir pasta downloads"
    - "abrir pasta documentos"
    """
    m = re.search(r"\babr(?:ir)?\b\s+(?:a\s+)?(?:pasta\s+)?(.+)$", cmd.strip().lower())
    if not m:
        return False
    target = m.group(1).strip()
    # Trim common filler words
    target = re.sub(r"^(a|o|os|as)\s+", "", target).strip()

    resolved = _user_folder(target)
    if not resolved:
        return False
    path, name = resolved
    _cmd_open_folder(path, name)
    return True


def execute_command(cmd: str, *, speak_on_fail: bool = True) -> bool:
    from jarvis.core import log, speak, update_status

    log.info("execute_command invoked with: %s", cmd)
    # Normalize transcription quirks (case/punctuation/common misspells)
    normalized = (cmd or "").strip().lower()
    normalized = re.sub(r"[.!?]+$", "", normalized)
    normalized = normalized.replace("crome", "chrome")

    # folder commands first (more specific intent)
    try:
        if _try_folder(normalized):
            return True
    except Exception:
        pass

    for pattern, handler in COMMAND_MAP.items():
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            log.info("pattern '%s' matched", pattern)
            handler(normalized)
            return True
    log.info("no pattern matched for command")
    if speak_on_fail:
        speak("Comando nao reconhecido. Tente: hora, data, Google, YouTube, clima, calculadora ou desligar.")
    update_status("Comando nao mapeado: " + normalized[:40])
    return False