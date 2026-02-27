import json
import os
import sys
import time
import threading

import numpy as np
import sounddevice as sd

from vosk import Model as VoskModel, KaldiRecognizer

from jarvis.config import (
    VOSK_MODEL_PATH,
    WAKE_WORD,
    SAMPLE_RATE,
    BLOCK_SIZE,
    CHANNELS,
    DTYPE,
    AUDIO_DEVICE,
    VAD_MAX_DURATION,
    VAD_MIN_SPEECH,
    VAD_MIN_SILENCE,
)
from jarvis.core import log, update_status, speak, add_history, _command_active, _shutdown, _vad_active, amplitude_queue
from jarvis.voice.vad import vad
from jarvis.voice.transcriber import whisper_asr
from jarvis.commands.registry import execute_command


class WakeWordListener:

    def __init__(self):
        if not os.path.isdir(VOSK_MODEL_PATH):
            msg = (
                f"[JARVIS] Modelo Vosk nao encontrado em '{VOSK_MODEL_PATH}'.\n"
                "Baixe em: https://alphacephei.com/vosk/models\n"
                "  vosk-model-small-pt-0.3  (extraia em models/vosk-pt)"
            )
            log.critical(msg)
            sys.exit(msg)

        self._model      = VoskModel(VOSK_MODEL_PATH)
        self._sr, self._dev = self._probe_device()
        # log all input devices to help the user choose if something goes wrong
        self._print_devices()
        update_status("Lista de dispositivos exibida no log (use JARVIS_AUDIO_DEVICE se precisar selecionar outro)")
        self._rec        = KaldiRecognizer(self._model, self._sr)
        self._rec.SetWords(False)
        self._last_trigger_ts: float = 0.0   # timestamp do último trigger (debounce)
        update_status(f"Dispositivo: {self._dev} @ {self._sr}Hz")

    def _print_devices(self):
        """Log available input devices for troubleshooting."""
        try:
            log.info("Audio input devices:")
            for i, d in enumerate(sd.query_devices()):
                if d.get("max_input_channels", 0) > 0:
                    log.info("    %d: %s (sr %s)", i, d.get("name"), d.get("default_samplerate"))
        except Exception as e:
            log.warning("Failed listing devices: %s", e)

    def _probe_device(self):
        # choose device from environment override if provided
        try:
            if AUDIO_DEVICE:
                try:
                    idx = int(AUDIO_DEVICE)
                except ValueError:
                    idx = None
                    for i, d in enumerate(sd.query_devices()):
                        if AUDIO_DEVICE.lower() in d.get("name","").lower() and d.get("max_input_channels",0) > 0:
                            idx = i
                            break
                log.info("Audio override request '%s' -> device index %s", AUDIO_DEVICE, idx)
            else:
                idx = sd.default.device[0]
            if idx is None:
                info = sd.query_devices(kind="input")
            else:
                info = sd.query_devices(idx, "input")
            return int(info.get("default_samplerate", SAMPLE_RATE)), info.get("name","?")
        except Exception as e:
            log.warning("Probe device: %s", e)
            return SAMPLE_RATE, "Padrao"

    def start(self):
        threading.Thread(target=self._loop, daemon=True, name="WakeWord").start()

    def _loop(self):
        def callback(indata, frames, time_, status):
            # monitor for complete silence so user knows if mic isn't working
            if _shutdown.is_set() or _command_active.is_set():
                return
            rms = int(np.sqrt(np.mean(np.frombuffer(bytes(indata), dtype=np.int16).astype(np.float32)**2)))
            amplitude_queue.put(min(rms, 3000))
            # simple silence detector that warns after several seconds
            if not hasattr(callback, "_silent_start"):
                callback._silent_start = None
            if rms < 500:
                if callback._silent_start is None:
                    callback._silent_start = time.time()
                elif time.time() - callback._silent_start > 5:
                    log.warning("Nenhum som detectado por >5s, verifique microfone/dispositivo")
                    update_status("Sem audio - verifique o microfone")
                    callback._silent_start = time.time()
            else:
                callback._silent_start = None
            raw = bytes(indata)
            try:
                if self._rec.AcceptWaveform(raw):
                    result = json.loads(self._rec.Result())
                    text   = result.get("text", "").lower()
                    if text:
                        update_status("... " + text)
                    if WAKE_WORD in text:
                        self._trigger()
                else:
                    partial = json.loads(self._rec.PartialResult()).get("partial", "").lower()
                    if partial:
                        update_status("... " + partial)
                    if WAKE_WORD in partial and not _command_active.is_set():
                        self._trigger()
            except Exception as e:
                log.error("WW callback: %s", e)

        try:
            with sd.RawInputStream(samplerate=self._sr, blocksize=BLOCK_SIZE,
                                   dtype=DTYPE, channels=CHANNELS, callback=callback):
                update_status("Aguardando wake word: " + WAKE_WORD.upper())
                while not _shutdown.is_set():
                    time.sleep(0.1)
        except sd.PortAudioError as e:
            log.critical("PortAudio: %s", e)
            update_status("ERRO de audio: " + str(e) + " (verifique dispositivo/microfone)")

    def _trigger(self):
        """Ativa o modo de comando com debounce de 2s para evitar double-trigger.

        O problema original: tanto o resultado final (Result) quanto o parcial
        (PartialResult) podiam acionar _trigger no mesmo frame de áudio, causando
        duas gravações simultâneas e dois TTS "Sim, senhor?" sobrepostos.
        """
        now = time.monotonic()
        if _command_active.is_set():
            return
        # ── Debounce: ignora acionamentos dentro de 2 segundos do último ──
        if now - self._last_trigger_ts < 2.0:
            log.debug("Wake word ignorada (debounce %.2fs)", now - self._last_trigger_ts)
            return
        self._last_trigger_ts = now
        _command_active.set()
        update_status("Wake word detectada!")
        speak("Sim, senhor?")
        threading.Thread(target=self._record_cmd, daemon=True, name="CMD").start()

    def _record_cmd(self):
        try:
            update_status("Ouvindo comando...")
            log.info("Comecando gravacao de comando (max_frames=%d, min_speech=%d)",
                     int(VAD_MAX_DURATION  * SAMPLE_RATE / BLOCK_SIZE),
                     int(VAD_MIN_SPEECH    * SAMPLE_RATE / BLOCK_SIZE))
            audio_buf:    list[np.ndarray] = []
            speech_frames = 0
            silence_frames= 0
            total_frames  = 0
            max_f   = int(VAD_MAX_DURATION  * SAMPLE_RATE / BLOCK_SIZE)
            min_sp  = int(VAD_MIN_SPEECH    * SAMPLE_RATE / BLOCK_SIZE)
            sil_thr = int(VAD_MIN_SILENCE   * SAMPLE_RATE / BLOCK_SIZE)
            vad.reset()

            def cb(indata, frames, t, status):
                nonlocal speech_frames, silence_frames, total_frames
                chunk = np.frombuffer(bytes(indata), dtype=np.int16).copy()
                rms   = int(np.sqrt(np.mean(chunk.astype(np.float32)**2)))
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

            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=BLOCK_SIZE,
                                   dtype=DTYPE, channels=CHANNELS, callback=cb):
                while True:
                    time.sleep(0.05)
                    if total_frames >= max_f:
                        update_status("Limite de tempo atingido")
                        break
                    if speech_frames >= min_sp and silence_frames >= sil_thr:
                        update_status("Fala encerrada — transcrevendo...")
                        break

            if speech_frames < min_sp:
                if total_frames > 0:
                    log.info("voz detectada (%d frames) abaixo do minimo (%d), tentando transcrever mesmo assim", speech_frames, min_sp)
                    update_status("Fala curta detectada, transcrevendo…")
                else:
                    update_status("Nenhuma fala detectada")
                    speak("Nao ouvi nada, senhor.")
                    return

            update_status("Transcrevendo com Whisper PT-BR...")
            full_audio = np.concatenate(audio_buf)
            if not whisper_asr.ready:
                update_status("Aguardando Whisper carregar...")
                whisper_asr.wait_ready(30)

            cmd = whisper_asr.transcribe(full_audio)
            if cmd:
                update_status("Comando: " + cmd)
                add_history(cmd)
                execute_command(cmd)
            else:
                update_status("Nao entendi o comando")
                speak("Desculpe, nao entendi.")
        except Exception as e:
            log.error("Record/transcribe: %s", e)
            update_status("ERRO: " + str(e))
        finally:
            _vad_active.clear()
            _command_active.clear()
            update_status("Aguardando wake word: " + WAKE_WORD.upper())
