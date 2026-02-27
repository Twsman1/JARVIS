import os

# audio / ASR configuration
WAKE_WORD = "acorde"                          # palavra de ativacao (Vosk)
VOSK_MODEL_PATH = "models/vosk-pt"            # modelo vosk-model-small-pt-0.3

# optional audio device override: index or substring of name
AUDIO_DEVICE = os.environ.get("JARVIS_AUDIO_DEVICE")

# faster-whisper model (tiny, base, small, medium)
WHISPER_MODEL = "small"
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