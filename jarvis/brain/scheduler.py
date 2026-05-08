# jarvis/brain/scheduler.py
#
# Agendador de tarefas e lembretes
# Permite ao JARVIS executar tarefas no futuro

import threading
import time
import uuid
import re
from jarvis import core

class Scheduler:
    """
    Gerenciador de tarefas agendadas.
    Permite agendar lembretes e tarefas para execução futura.
    """

    def __init__(self, speak_callback):
        self.speak = speak_callback
        self._tasks = {}  # {task_id: {"timer": Timer, "description": str, "scheduled_time": float}}
        self._lock = threading.Lock()
        core.log.info("Agendador inicializado")

    def remind_in(self, description: str, minutes: float) -> str:
        """
        Agenda um lembrete para daqui a N minutos.

        Args:
            description: Descrição do lembrete
            minutes: Minutos até o disparo

        Returns:
            Mensagem de confirmação
        """
        with self._lock:
            task_id = str(uuid.uuid4())[:8]
            delay_seconds = minutes * 60

            # Criar timer
            timer = threading.Timer(delay_seconds, self._fire, args=[task_id, description])
            timer.daemon = True
            timer.start()

            # Armazenar tarefa
            scheduled_time = time.time() + delay_seconds
            self._tasks[task_id] = {
                "timer": timer,
                "description": description,
                "scheduled_time": scheduled_time
            }

            core.log.info(f"Lembrete agendado: '{description}' em {minutes:.1f} minutos (ID: {task_id})")
            return f"Lembrete agendado: '{description}' em {minutes:.0f} minuto(s)."

    def cancel(self, task_id: str) -> str:
        """
        Cancela um lembrete agendado.

        Args:
            task_id: ID do lembrete (ou parte dele)

        Returns:
            Mensagem de resultado
        """
        with self._lock:
            # Procurar tarefa por ID (ou substring)
            found_task_id = None
            for tid, task_info in self._tasks.items():
                if task_id in tid:
                    found_task_id = tid
                    break

            if found_task_id:
                task_info = self._tasks[found_task_id]
                task_info["timer"].cancel()
                del self._tasks[found_task_id]
                core.log.info(f"Lembrete cancelado: {task_info['description']}")
                return f"Lembrete cancelado: {task_info['description']}"
            else:
                return "Nenhum lembrete encontrado com esse ID."

    def list_tasks(self) -> str:
        """
        Lista todas as tarefas pendentes.

        Returns:
            String formatada com tarefas pendentes
        """
        with self._lock:
            if not self._tasks:
                return "Nenhum lembrete agendado."

            current_time = time.time()
            result = "Lembretes pendentes:\n"

            for task_id, task_info in self._tasks.items():
                remaining_minutes = (task_info["scheduled_time"] - current_time) / 60
                if remaining_minutes > 0:
                    result += f"- {task_info['description']} (em {remaining_minutes:.1f} min, ID: {task_id})\n"
                else:
                    result += f"- {task_info['description']} (atrasado, ID: {task_id})\n"

            return result.strip()

    def _fire(self, task_id: str, description: str):
        """
        Dispara um lembrete (chamado pelo timer).
        """
        with self._lock:
            # Remover da lista (se ainda existir)
            if task_id in self._tasks:
                del self._tasks[task_id]

        core.log.info(f"Lembrete disparado: {description}")
        self.speak(f"Lembrete, senhor: {description}")

    def parse_reminder_command(self, text: str) -> tuple[bool, str]:
        """
        Tenta extrair um comando de lembrete do texto.

        Args:
            text: Texto do usuário

        Returns:
            (is_reminder, response_message)
        """
        text_lower = text.lower().strip()

        # Padrões de lembrete
        patterns = [
            # "me lembra de {X} em {N} minutos"
            r'me lembra de (.+?) em (\d+(?:\.\d+)?) minutos?',
            # "lembra em {N} minutos: {X}"
            r'lembra em (\d+(?:\.\d+)?) minutos?:\s*(.+)',
            # "daqui a {N} minutos, {X}"
            r'daqui a (\d+(?:\.\d+)?) minutos?, (.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                if len(match.groups()) == 2:
                    # Padrão 1: "me lembra de X em N minutos"
                    task = match.group(1).strip()
                    minutes = float(match.group(2))
                else:
                    # Padrões 2/3: "lembra em N: X" ou "daqui a N, X"
                    minutes = float(match.group(1))
                    task = match.group(2).strip()

                response = self.remind_in(task, minutes)
                return True, response

        # Comandos de listagem
        if any(cmd in text_lower for cmd in ["listar lembretes", "lembretes", "quais lembretes"]):
            response = self.list_tasks()
            return True, response

        # Comando de cancelamento
        cancel_match = re.search(r'cancelar?\s+(?:lembrete\s+)?(\w+)', text_lower)
        if cancel_match:
            task_id = cancel_match.group(1)
            response = self.cancel(task_id)
            return True, response

        return False, ""