import re

from .handlers import (
    _cmd_hora,
    _cmd_data,
    _cmd_open,
    _cmd_calculator,
    _cmd_standby,
    _cmd_shutdown,
    _cmd_joke,
    _cmd_version,
)

COMMAND_MAP = {
    r"\bhoras?\b":                   lambda _: _cmd_hora(),
    r"\bdata\b|\bdia\b":             lambda _: _cmd_data(),
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


def execute_command(cmd: str):
    from jarvis.core import log, speak, update_status

    log.info("execute_command invoked with: %s", cmd)
    for pattern, handler in COMMAND_MAP.items():
        if re.search(pattern, cmd):
            log.info("pattern '%s' matched", pattern)
            handler(cmd)
            return
    log.info("no pattern matched for command")
    speak("Comando nao reconhecido. Tente: hora, data, Google, YouTube, clima, calculadora ou desligar.")
    update_status("Comando nao mapeado: " + cmd[:40])