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
# text-to-speech helper thread
# ---------------------------------------------------------------------------

# The original single-file version drove pyttsx3 directly from the main loop.
# After refactoring we lost the consumer, so synth output was never played.
# Start a daemon thread here that reads from _tts_queue and speaks via pyttsx3.
try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    # attempt to pick a British‑English male voice such as "James" for a JARVIS‑like tone
    try:
        voices = _tts_engine.getProperty("voices")
        log.info("TTS voices available:")
        for v in voices:
            log.info("    %s (%s) languages=%s", v.name, v.id, getattr(v, 'languages', None))
        # first try for an explicitly requested voice (Daniel), else fall back to
        # a UK male voice such as James.
        chosen = None
        for v in voices:
            if "daniel" in v.name.lower():
                chosen = v
                break
        if not chosen:
            for v in voices:
                if "james" in v.name.lower() or "uk" in v.id.lower():
                    chosen = v
                    break
        if chosen:
            _tts_engine.setProperty("voice", chosen.id)
            log.info("TTS default voice set to %s", chosen.name)
    except Exception as ve:
        log.warning("Could not enumerate/set TTS voice: %s", ve)
except Exception as e:
    log = logging.getLogger("JARVIS")
    log.warning("Failed to initialize pyttsx3: %s", e)
    _tts_engine = None


def _tts_worker():
    if _tts_engine is None:
        log.warning("TTS engine not available, speech will be silent")
        return
    while True:
        text = _tts_queue.get()
        if text is None:
            break
        try:
            log.debug("TTS speaking: %s", text)
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        except Exception as e:
            log.error("TTS error: %s", e)

# launch worker thread silently (daemon so it won't block shutdown)
threading.Thread(target=_tts_worker, daemon=True, name="TTS").start()

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
