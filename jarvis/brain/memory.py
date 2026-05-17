import json
import threading
from pathlib import Path
from jarvis import core
import os
import time
import tempfile

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
        # Choose a memory file. When running under pytest, prefer a
        # per-process temp file to avoid file-locking conflicts between
        # test runs and the user's persistent memory.
        default_path = Path("jarvis/data")
        default_path.mkdir(parents=True, exist_ok=True)
        if os.environ.get("PYTEST_CURRENT_TEST"):
            tmpdir = Path(tempfile.gettempdir())
            self._memory_file = tmpdir / f"jarvis_memory_{os.getpid()}.json"
        else:
            self._memory_file = Path("jarvis/data/memory.json")

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
        # Try to remove the memory file. On Windows the file may be briefly
        # locked by a background writer thread; retry for a short period.
        if self._memory_file.exists():
            deadline = time.time() + 1.5
            while time.time() < deadline:
                try:
                    self._memory_file.unlink()
                    break
                except PermissionError:
                    time.sleep(0.05)
                except Exception as e:
                    core.log.info(f"Erro ao deletar arquivo de memória: {e}")
                    break
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
            # Write to a temporary file and atomically replace to avoid
            # leaving the file locked on Windows.
            self._memory_file.parent.mkdir(parents=True, exist_ok=True)
            # Create a unique temporary file to avoid collisions between
            # concurrent writers or other processes scanning the temp dir.
            with tempfile.NamedTemporaryFile('w', delete=False, dir=str(self._memory_file.parent), encoding='utf-8') as tf:
                json.dump(data, tf, indent=2, ensure_ascii=False)
                tmp = Path(tf.name)
            try:
                os.replace(tmp, self._memory_file)
            except Exception:
                # Fallback: try removing target then replacing
                try:
                    if self._memory_file.exists():
                        self._memory_file.unlink()
                    os.replace(tmp, self._memory_file)
                except Exception as e:
                    core.log.info(f"Erro ao mover arquivo de memória: {e}")
        except Exception as e:
            core.log.info(f"Erro ao salvar memória: {e}")

    def _load(self):
        if not self._memory_file.exists():
            return
        try:
            with open(self._memory_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._history = data.get("history", [])
        except Exception as e:
            core.log.info(f"Erro ao carregar memória: {e}")