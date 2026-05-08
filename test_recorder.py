from jarvis.voice.recorder import AudioRecorder
import numpy as np

print("Testando gravação... fale algo e pare de falar.")
recorder = AudioRecorder()
audio = recorder.record()
print(f"Áudio capturado: {len(audio)} samples ({len(audio)/16000:.1f} segundos)")
assert len(audio) > 0, "Nenhum áudio capturado!"
print("✅ Recorder OK")