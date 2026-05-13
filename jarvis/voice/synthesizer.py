import threading
import io
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
import sounddevice as sd
from piper import PiperVoice
from jarvis import core
from jarvis.hud import state

MODEL_PATH = Path("jarvis/data/voices/pt_BR-faber-medium.onnx")
CONFIG_PATH = Path("jarvis/data/voices/pt_BR-faber-medium.onnx.json")

@dataclass
class TTSResult:
    """Result of a text-to-speech synthesis - inspired by OpenJarvis patterns."""
    audio: bytes
    format: str = "wav"
    duration_seconds: float = 0.0
    voice_id: str = ""
    sample_rate: int = 22050
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class TTSBackend:
    """Abstract base class for TTS backends - OpenJarvis pattern."""

    backend_id: str = ""

    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize text to audio."""
        raise NotImplementedError

    def available_voices(self) -> List[str]:
        """Return list of available voice IDs."""
        raise NotImplementedError

    def health(self) -> bool:
        """Check if the backend is ready."""
        raise NotImplementedError

class PiperTTSBackend(TTSBackend):
    """Piper TTS backend - local neural voice synthesis."""

    backend_id = "piper"

    def __init__(self, model_path: Path = MODEL_PATH, config_path: Path = CONFIG_PATH):
        self.model_path = model_path
        self.config_path = config_path
        self._voice = None
        self._load_voice()

    def _load_voice(self):
        """Load the Piper voice model."""
        try:
            if not self.model_path.exists() or not self.config_path.exists():
                error_msg = f"Arquivos de voz não encontrados: {self.model_path} ou {self.config_path}"
                core.log.info(error_msg)
                raise FileNotFoundError(error_msg)
            self._voice = PiperVoice.load(str(self.model_path), config_path=str(self.config_path))
            core.log.info("Voz Piper carregada com sucesso")
        except Exception as e:
            core.log.info(f"Erro ao carregar voz Piper: {e}")
            self._voice = None

    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize text using Piper."""
        if self._voice is None:
            raise RuntimeError("Voz Piper não carregada")

        try:
            # Synthesize to PCM chunks
            chunks = list(self._voice.synthesize(text))
            if not chunks:
                return TTSResult(audio=b"", format="wav", voice_id="pt_BR-faber-medium")

            sample_rate = chunks[0].sample_rate or 22050
            audio_data = []

            for ch in chunks:
                # Use float32 array
                a = ch.audio_float_array
                if a is None:
                    # Fallback to int16 -> float32
                    ai16 = ch.audio_int16_array
                    if ai16 is None:
                        continue
                    a = ai16.astype("float32") / 32768.0
                audio_data.append(a)

            if not audio_data:
                return TTSResult(audio=b"", format="wav", voice_id="pt_BR-faber-medium")

            # Convert to WAV bytes
            import numpy as np
            audio_f = np.concatenate(audio_data)

            # Create WAV file in memory
            buf = io.BytesIO()
            import soundfile as sf
            sf.write(buf, audio_f, int(sample_rate), format='WAV')
            buf.seek(0)

            duration = len(audio_f) / sample_rate

            return TTSResult(
                audio=buf.read(),
                format="wav",
                duration_seconds=duration,
                voice_id="pt_BR-faber-medium",
                sample_rate=sample_rate,
                metadata={"backend": "piper"}
            )

        except Exception as e:
            core.log.info(f"Erro na síntese Piper: {e}")
            raise

    def available_voices(self) -> List[str]:
        """Return available Piper voices."""
        return ["pt_BR-faber-medium"]  # Currently only one voice loaded

    def health(self) -> bool:
        """Check if Piper voice is loaded."""
        return self._voice is not None

class FallbackTTSBackend(TTSBackend):
    """Fallback TTS using pyttsx3 - system TTS."""

    backend_id = "pyttsx3"

    def __init__(self):
        self._engine = None
        self._load_engine()

    def _load_engine(self):
        """Load pyttsx3 engine."""
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            # Configure for Portuguese if available
            voices = self._engine.getProperty('voices')
            for voice in voices:
                if 'portuguese' in voice.name.lower() or 'pt' in voice.name.lower():
                    self._engine.setProperty('voice', voice.id)
                    break
            core.log.info("Engine pyttsx3 carregado como fallback")
        except Exception as e:
            core.log.info(f"Erro ao carregar pyttsx3: {e}")
            self._engine = None

    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Synthesize using pyttsx3."""
        if self._engine is None:
            raise RuntimeError("Engine pyttsx3 não disponível")

        # pyttsx3 doesn't provide audio bytes directly, so we return empty
        # The actual playback happens in the speak_worker
        return TTSResult(
            audio=b"",  # pyttsx3 plays directly
            format="system",
            duration_seconds=len(text) * 0.1,  # Rough estimate
            voice_id="system",
            metadata={"backend": "pyttsx3", "text": text}
        )

    def available_voices(self) -> List[str]:
        """Return available system voices."""
        if self._engine is None:
            return []
        try:
            voices = self._engine.getProperty('voices')
            return [voice.name for voice in voices]
        except:
            return ["system"]

    def health(self) -> bool:
        """Check if pyttsx3 engine is available."""
        return self._engine is not None

class Synthesizer:
    def __init__(self):
        self.backends = {}
        self.primary_backend = None

        # Try to load Piper first
        try:
            self.backends["piper"] = PiperTTSBackend()
            if self.backends["piper"].health():
                self.primary_backend = "piper"
                core.log.info("Sintetizador usando backend Piper (primário)")
        except Exception as e:
            core.log.info(f"Backend Piper falhou: {e}")

        # Fallback to pyttsx3
        if self.primary_backend is None:
            try:
                self.backends["pyttsx3"] = FallbackTTSBackend()
                if self.backends["pyttsx3"].health():
                    self.primary_backend = "pyttsx3"
                    core.log.info("Sintetizador usando backend pyttsx3 (fallback)")
            except Exception as e:
                core.log.info(f"Backend pyttsx3 falhou: {e}")

        if self.primary_backend is None:
            raise RuntimeError("Nenhum backend TTS disponível")

        core.log.info(f"Sintetizador de voz pronto com backend: {self.primary_backend}")

    def start(self):
        self.thread = threading.Thread(target=self.speak_worker, daemon=True)
        self.thread.start()

    def speak_worker(self):
        while True:
            try:
                item = core._tts_queue.get()
                if item is None:
                    core.log.info("Encerrando sintetizador de voz")
                    break
                if isinstance(item, str):
                    self._synthesize_and_play(item)
            except Exception as e:
                core.log.info(f"Erro no sintetizador: {e}")

    def _synthesize_and_play(self, text: str):
        try:
            state.set_state(state.SPEAKING, text[:30])

            backend = self.backends.get(self.primary_backend)
            if backend is None:
                core.log.info("Nenhum backend TTS disponível")
                return

            result = backend.synthesize(text)

            if result.format == "system":
                # pyttsx3 plays directly
                if self.primary_backend == "pyttsx3":
                    self.backends["pyttsx3"]._engine.say(text)
                    self.backends["pyttsx3"]._engine.runAndWait()
            else:
                # Play audio bytes
                import numpy as np
                import soundfile as sf

                # Load audio from bytes
                buf = io.BytesIO(result.audio)
                audio_data, sample_rate = sf.read(buf, dtype='float32')

                sd.play(audio_data, samplerate=result.sample_rate)
                sd.wait()

        except Exception as e:
            core.log.info(f"Erro na síntese: {e}")
        finally:
            state.set_state(state.IDLE)

    def get_available_voices(self) -> List[str]:
        """Get all available voices across backends."""
        voices = []
        for backend in self.backends.values():
            voices.extend(backend.available_voices())
        return list(set(voices))  # Remove duplicates