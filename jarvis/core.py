import logging
import logging.handlers
import queue
import threading

# ---------------------------------------------------------------------------
# logging
# ---------------------------------------------------------------------------

_log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

_rotating_handler = logging.handlers.RotatingFileHandler(
    "jarvis.log",
    maxBytes=5 * 1024 * 1024,   # 5 MB por arquivo
    backupCount=3,              # mantém jarvis.log, .1, .2, .3
    encoding="utf-8",
)
_rotating_handler.setFormatter(_log_formatter)

_stream_handler = logging.StreamHandler()
_stream_handler.setFormatter(_log_formatter)

logging.root.setLevel(logging.INFO)
logging.root.addHandler(_rotating_handler)
logging.root.addHandler(_stream_handler)

log = logging.getLogger("JARVIS")
log.info("Sistema de log iniciado — rotação ativa (5MB × 3 backups)")

# ---------------------------------------------------------------------------
# shared events / queues
# ---------------------------------------------------------------------------

_command_active = threading.Event()
_shutdown = threading.Event()
_vad_active = threading.Event()

# used by TTS thread
_tts_queue: queue.Queue = queue.Queue()

status_queue: queue.Queue = queue.Queue()
history_queue: queue.Queue = queue.Queue()
amplitude_queue: queue.Queue = queue.Queue()

# ---------------------------------------------------------------------------
# text-to-speech helper (now handled by Synthesizer in separate thread)
# ---------------------------------------------------------------------------

def speak(text: str):
    """Enfileira texto para síntese de voz. Não bloqueia."""
    log(f"TTS enfileirado: {text}")
    _tts_queue.put(text)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def speak(text: str):
    """Voice output (thread-safe)."""
    log.info("FALA: %s", text)
    _tts_queue.put(text)


def update_status(text: str):
    status_queue.put(text)
    log.info("STATUS: %s", text)


def add_history(cmd: str):
    history_queue.put(cmd)
