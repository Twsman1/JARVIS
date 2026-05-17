import os

# audio / ASR configuration
WAKE_WORD = "acorde"                          # palavra de ativacao (Vosk)
VOSK_MODEL_PATH = "models/vosk-pt"            # modelo vosk-model-small-pt-0.3

# optional audio device override: index or substring of name
AUDIO_DEVICE = os.environ.get("JARVIS_AUDIO_DEVICE")

# Local LLM engine selection for offline-first usage.
# Set JARVIS_LLM_ENGINE=ollama to use Ollama local server,
# or JARVIS_LLM_ENGINE=openjarvis to use the OpenJarvis SDK source tree.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_ENGINE = os.environ.get("JARVIS_LLM_ENGINE", "ollama")
JARVIS_OPENJARVIS_PATH = os.environ.get(
    "JARVIS_OPENJARVIS_PATH",
    "openjarvis/OpenJarvis/src",
)
JARVIS_OPENJARVIS_CONFIG = os.environ.get(
    "JARVIS_OPENJARVIS_CONFIG",
    "openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml",
)

# faster-whisper model.
#
# To avoid any online requests, download the model locally and point WHISPER_MODEL
# to a local folder (default: models/whisper-small). If that folder does not
# exist, it falls back to the named model (e.g. "small"), which may trigger
# Hugging Face hub requests.
WHISPER_LOCAL_DIR = os.environ.get("JARVIS_WHISPER_DIR", "models/whisper-small")
_whisper_bin = os.path.join(WHISPER_LOCAL_DIR, "model.bin")
WHISPER_MODEL = WHISPER_LOCAL_DIR if os.path.isfile(_whisper_bin) else "small"
WHISPER_LANG = "pt"

# audio sampling
SAMPLE_RATE = 16000
BLOCK_SIZE = 512          # ~32ms por frame (melhor para VAD)
CHANNELS = 1
DTYPE = "int16"

# Silero-VAD parameters
VAD_THRESHOLD = 0.45      # 0-1; maior = menos sensivel
VAD_MIN_SILENCE = 0.5     # segundos de silencio para encerrar comando
VAD_MAX_DURATION = 8.0    # segundos max de gravacao de comando
VAD_MIN_SPEECH = 0.2      # segundos minimos de fala antes de aceitar

# Modelo LLM padrão (trocar aqui para mudar em todo o projeto)
# Use a env var JARVIS_LLM_MODEL to override, default to a small local starter model.
LLM_MODEL = os.environ.get("JARVIS_LLM_MODEL", "qwen3:0.6b")

# Alternativas:
# LLM_MODEL = "phi3"         # mais leve
# LLM_MODEL = "qwen2:7b"    # melhor PT-BR

# Parâmetros do LLM
LLM_TEMPERATURE = 0.7
LLM_MAX_TOKENS = 300

# TTS Piper
PIPER_MODEL_PATH = "jarvis/data/voices/pt_BR-faber-medium.onnx"
PIPER_CONFIG_PATH = "jarvis/data/voices/pt_BR-faber-medium.onnx.json"

# Gravação de áudio
RECORDER_SAMPLE_RATE = 16000
RECORDER_MAX_SILENCE_MS = 900
RECORDER_MAX_DURATION_S = 15

# Memória
MEMORY_MAX_TURNS = 20
MEMORY_FILE = "jarvis/data/memory.json"