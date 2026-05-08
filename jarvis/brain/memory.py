import json
import threading
from pathlib import Path
from jarvis import core

MEMORY_FILE = Path("jarvis/data/memory.json")
MAX_HISTORY_TURNS = 20  # pares user+assistant

SYSTEM_PROMPT = """Você é JARVIS, assistente pessoal de inteligência artificial.
Você foi criado para ajudar seu criador com tarefas no computador, responder perguntas,
buscar informações e executar ações quando solicitado.

Regras de comportamento:
- Responda SEMPRE em português do Brasil
- Seja direto e conciso — respostas de no máximo 3 frases quando possível
- Use linguagem natural, não robótica
- Chame o usuário de "senhor" ocasionalmente para manter o estilo JARVIS
- Se não souber algo, diga claramente que não sabe
- Quando executar uma ação, confirme brevemente o que fez
- Nunca invente informações factuais"""

class Memory:
    def __init__(self, router=None):
        Path("jarvis/data").mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._history = []
        self.router = router
        self._load()
        core.log.info(f"Memória carregada com {len(self._history)} mensagens")

    def get_messages(self) -> list:
        with self._lock:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            if self.router:
                messages.append({"role": "system", "content": self.router.get_system_addon()})
            messages.extend(self._history.copy())
            return messages

    def add_user(self, text: str):
        with self._lock:
            self._history.append({"role": "user", "content": text})
            self._trim()
        self._save()

    def add_assistant(self, text: str):
        with self._lock:
            self._history.append({"role": "assistant", "content": text})
            self._trim()
        self._save()

    def clear(self):
        with self._lock:
            self._history.clear()
        try:
            if MEMORY_FILE.exists():
                MEMORY_FILE.unlink()
        except Exception as e:
            core.log.info(f"Erro ao deletar arquivo de memória: {e}")
        core.log.info("Memória limpa")

    def _trim(self):
        if len(self._history) > MAX_HISTORY_TURNS * 2:
            self._history = self._history[-(MAX_HISTORY_TURNS * 2):]

    def _save(self):
        threading.Thread(target=self._save_to_disk, daemon=True).start()

    def _save_to_disk(self):
        try:
            with self._lock:
                history_copy = self._history.copy()
            data = {"history": history_copy}
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            core.log.info(f"Erro ao salvar memória: {e}")

    def _load(self):
        if not MEMORY_FILE.exists():
            return
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._history = data.get("history", [])
        except Exception as e:
            core.log.info(f"Erro ao carregar memória: {e}")