# test_scheduler.py (temporário, deletar após teste)

import time
from jarvis.brain.scheduler import Scheduler
from jarvis import core

def mock_speak(text):
    print(f"[FALA] {text}")

s = Scheduler(speak_callback=mock_speak)

# Agendar lembrete em 0.1 minutos (~6 segundos)
r = s.remind_in("beber água", 0.1)
print(f"Agendado: {r}")
print(f"Lista: {s.list_tasks()}")

print("Aguardando lembrete...")
time.sleep(8)
print("✅ Scheduler OK")