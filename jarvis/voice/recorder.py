import sounddevice as sd
import numpy as np
import webrtcvad
import queue
import threading
from jarvis import core

SAMPLE_RATE = 16000
CHANNELS = 1
CHUNK_MS = 30
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_MS / 1000)  # 480 samples por chunk
MAX_SILENCE_FRAMES = 30   # 30 * 30ms = 900ms de silêncio para parar
MAX_RECORD_SECONDS = 15   # timeout máximo

class AudioRecorder:
    def __init__(self, vad_aggressiveness=2):
        self.vad = webrtcvad.Vad(vad_aggressiveness)
        self._audio_queue = queue.Queue()

    def record(self) -> np.ndarray:
        core.log("Iniciando gravação de áudio...")
        audio_frames = []
        silence_frames = 0
        start_time = threading.Timer(MAX_RECORD_SECONDS, lambda: None)
        start_time.start()

        def callback(indata, frames, time, status):
            if status:
                core.log(f"Status do stream: {status}")
            self._audio_queue.put(indata.copy())

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype='int16', blocksize=CHUNK_SAMPLES, callback=callback):
            while not start_time.finished.is_set():
                try:
                    chunk = self._audio_queue.get(timeout=0.1)
                    chunk_bytes = chunk.tobytes()
                    if self._is_speech(chunk_bytes):
                        audio_frames.append(chunk)
                        silence_frames = 0
                    else:
                        silence_frames += 1
                        if silence_frames >= MAX_SILENCE_FRAMES:
                            break
                except queue.Empty:
                    continue

        start_time.cancel()
        if audio_frames:
            audio = np.concatenate(audio_frames)
        else:
            audio = np.array([], dtype=np.int16)
        core.log(f"Gravação finalizada: {len(audio)} samples")
        return audio

    def _is_speech(self, frame_bytes: bytes) -> bool:
        return self.vad.is_speech(frame_bytes, SAMPLE_RATE)