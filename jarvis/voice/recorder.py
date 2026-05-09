import sounddevice as sd
import numpy as np
import queue
import threading
from jarvis import core

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)  # 480 samples por chunk
MAX_SILENCE_FRAMES = 30   # 30 * 30ms = 900ms de silêncio para parar
MAX_RECORD_SECONDS = 3   # timeout máximo

class AudioRecorder:
    def __init__(self, vad_aggressiveness=2):
        # self.vad = webrtcvad.Vad(vad_aggressiveness)
        self.vad = None  # Disabled due to import issues
        self._audio_queue = queue.Queue()

    def record(self) -> np.ndarray:
        core.log.info("Iniciando gravação de áudio...")
        audio_frames = []
        start_time = threading.Timer(MAX_RECORD_SECONDS, lambda: None)
        start_time.start()

        def callback(indata, frames, time, status):
            if status:
                core.log.info(f"Status do stream: {status}")
            self._audio_queue.put(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', blocksize=CHUNK_SAMPLES, callback=callback):
            while not start_time.finished.is_set():
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                    audio_frames.append(chunk)
                except queue.Empty:
                    continue

        start_time.cancel()
        if audio_frames:
            audio = np.concatenate(audio_frames)
        else:
            audio = np.array([], dtype=np.int16)
        core.log.info(f"Gravação finalizada: {len(audio)} samples")
        return audio