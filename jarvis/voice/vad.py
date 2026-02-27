import threading
import numpy as np

from jarvis.core import log
from jarvis.config import VAD_THRESHOLD, SAMPLE_RATE, VAD_MIN_SILENCE


class SileroVAD:
    def __init__(self):
        self._ready = False
        threading.Thread(target=self._load, daemon=True, name="VAD-load").start()

    def _load(self):
        try:
            import torch
            self.model, utils = torch.hub.load(
                repo_or_dir="snakers4/silero-vad",
                model="silero_vad",
                force_reload=False,
                trust_repo=True,
            )
            (self.get_speech_timestamps,
             self.save_audio, self.read_audio,
             self.VADIterator, self.collect_chunks) = utils
            self._vad_iter = self.VADIterator(
                self.model,
                threshold=VAD_THRESHOLD,
                sampling_rate=SAMPLE_RATE,
                min_silence_duration_ms=int(VAD_MIN_SILENCE * 1000),
                speech_pad_ms=60,
            )
            self._ready = True
            log.info("Silero-VAD carregado.")
        except Exception as e:
            log.warning("Silero-VAD indisponivel (%s) — usando fallback de amplitude", e)

    @property
    def ready(self):
        return self._ready

    def is_speech(self, pcm_int16: np.ndarray) -> bool:
        if not self._ready:
            return self._amp_fallback(pcm_int16)
        try:
            import torch
            af = pcm_int16.astype(np.float32) / 32768.0
            r  = self._vad_iter(torch.from_numpy(af), return_seconds=False)
            return r is not None
        except Exception:
            return self._amp_fallback(pcm_int16)

    def reset(self):
        if self._ready:
            try:
                self._vad_iter.reset_states()
            except Exception:
                pass

    @staticmethod
    def _amp_fallback(pcm: np.ndarray) -> bool:
        rms = np.sqrt(np.mean(pcm.astype(np.float32) ** 2))
        return rms > 600


# single shared instance
vad = SileroVAD()
