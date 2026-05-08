import time
from jarvis.voice.synthesizer import Synthesizer
from jarvis import core

synth = Synthesizer()
synth.start()
time.sleep(0.5)

core.speak("Teste de síntese de voz. JARVIS operacional.")
time.sleep(5)  # aguardar síntese

core._tts_queue.put(None)  # encerrar worker
print("✅ Synthesizer OK")