import os

# audio / ASR configuration
WAKE_WORD = "acorde"                          # palavra de ativacao (Vosk)
VOSK_MODEL_PATH = "models/vosk-pt"            # modelo vosk-model-small-pt-0.3

# optional audio device override: index or substring of name
AUDIO_DEVICE = os.environ.get("JARVIS_AUDIO_DEVICE")

# Local LLM engine selection for offline-first usage.
# Set JARVIS_LLM_ENGINE=openjarvis to use the OpenJarvis SDK source tree,
# or JARVIS_LLM_ENGINE=ollama to use a local Ollama server.
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
LLM_ENGINE = os.environ.get("JARVIS_LLM_ENGINE", "openjarvis")
JARVIS_OPENJARVIS_PATH = os.environ.get(
    "JARVIS_OPENJARVIS_PATH",
    "openjarvis/OpenJarvis/src",
)
_default_openjarvis_config = os.path.expanduser("~/.openjarvis/config.toml")
if not os.path.isfile(_default_openjarvis_config):
    _default_openjarvis_config = os.path.normpath(
        os.path.abspath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "openjarvis",
                "OpenJarvis",
                "configs",
                "openjarvis",
                "examples",
                "chat-simple.toml",
            )
        )
    )

JARVIS_OPENJARVIS_CONFIG = os.environ.get(
    "JARVIS_OPENJARVIS_CONFIG",
    _default_openjarvis_config,
)

# faster-whisper model.
#
# To keep Jarvis fully offline, this project requires a downloaded local Whisper
# model at the path configured by JARVIS_WHISPER_DIR. If the model is missing,
# Jarvis will not fall back to Hugging Face hub downloads.
WHISPER_LOCAL_DIR = os.environ.get("JARVIS_WHISPER_DIR", "models/whisper-small")


def _find_whisper_model_in_hf_cache(path: str) -> str | None:
    """Search the local Hugging Face hub cache for a cached Whisper model."""
    hf_home = os.environ.get("HF_HOME", os.path.expanduser("~/.cache/huggingface"))
    cache_root = os.path.join(hf_home, "hub")
    if not os.path.isdir(cache_root):
        return None

    target_name = os.path.basename(path).lower()
    if not target_name:
        return None

    for root, _, files in os.walk(cache_root):
        if "model.bin" in files and target_name in root.lower():
            return root
    return None


def _find_whisper_model_dir(path: str) -> str | None:
    """Resolve a Whisper model directory by locating model.bin in the tree."""
    if os.path.isfile(path):
        return os.path.dirname(path)

    if os.path.isdir(path):
        candidate = os.path.join(path, "model.bin")
        if os.path.isfile(candidate):
            return path

        for root, _, files in os.walk(path):
            if "model.bin" in files:
                return root

    return _find_whisper_model_in_hf_cache(path)


WHISPER_MODEL = _find_whisper_model_dir(WHISPER_LOCAL_DIR)
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