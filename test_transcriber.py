from jarvis.voice.recorder import AudioRecorder
from jarvis.voice.transcriber import Transcriber

print("Carregando Whisper...")
t = Transcriber()
print("Fale um comando após o beep...")
import time; time.sleep(1); print("FALE AGORA")
r = AudioRecorder()
audio = r.record()
text = t.transcribe(audio)
print(f"Transcrito: '{text}'")
assert len(text) > 0, "Transcrição vazia!"
print("✅ Transcriber OK")