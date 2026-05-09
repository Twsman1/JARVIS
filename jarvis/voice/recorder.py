import time

import numpy as np
import sounddevice as sd

from jarvis import core
from jarvis.config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    CHANNELS,
    DTYPE,
    VAD_MAX_DURATION,
    VAD_MIN_SPEECH,
    VAD_MIN_SILENCE,
)
from jarvis.core import _vad_active, amplitude_queue
from jarvis.voice.vad import vad

class AudioRecorder:
    def __init__(self, vad_aggressiveness=2):
        # self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.vad = None  # Disabled due to import issues

    def record(self) -> np.ndarray:
        """
        Record audio until VAD detects end-of-speech or a max duration.

        Previous implementation used a fixed ~3s timer and often cut the user
        off, making it seem like Jarvis "stopped listening" after the wake word.
        """
        core.log.info("Iniciando gravação de comando (VAD)...")

        audio_buf: list[np.ndarray] = []
        speech_frames = 0
        silence_frames = 0
        total_frames = 0

        max_f = int(VAD_MAX_DURATION * SAMPLE_RATE / BLOCK_SIZE)
        min_sp = int(VAD_MIN_SPEECH * SAMPLE_RATE / BLOCK_SIZE)
        sil_thr = int(VAD_MIN_SILENCE * SAMPLE_RATE / BLOCK_SIZE)

        vad.reset()

        def cb(indata, frames, t, status):
            nonlocal speech_frames, silence_frames, total_frames
            if status:
                core.log.info("Status do stream: %s", status)
            chunk = np.frombuffer(bytes(indata), dtype=np.int16).copy()
            rms = int(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))
            amplitude_queue.put(min(rms, 3000))
            audio_buf.append(chunk)
            total_frames += 1
            if vad.is_speech(chunk):
                speech_frames += 1
                silence_frames = 0
                _vad_active.set()
            else:
                silence_frames += 1
                if silence_frames > 4:
                    _vad_active.clear()

        start = time.monotonic()
        try:
            with sd.RawInputStream(
                samplerate=SAMPLE_RATE,
                blocksize=BLOCK_SIZE,
                dtype=DTYPE,
                channels=CHANNELS,
                callback=cb,
            ):
                while True:
                    time.sleep(0.05)
                    if total_frames >= max_f:
                        core.update_status("Limite de tempo atingido")
                        break
                    if speech_frames >= min_sp and silence_frames >= sil_thr:
                        core.update_status("Fala encerrada — transcrevendo...")
                        break
                    # safety: if stream yields nothing for a while
                    if time.monotonic() - start > max(VAD_MAX_DURATION + 1.0, 2.0) and total_frames == 0:
                        break
        finally:
            _vad_active.clear()

        if not audio_buf:
            core.log.info("Gravação finalizada (sem áudio captado)")
            return np.array([], dtype=np.int16)

        audio = np.concatenate(audio_buf)
        core.log.info(
            "Gravação finalizada: %d samples (speech_frames=%d, total_frames=%d, dt=%.2fs)",
            len(audio),
            speech_frames,
            total_frames,
            time.monotonic() - start,
        )
        return audio