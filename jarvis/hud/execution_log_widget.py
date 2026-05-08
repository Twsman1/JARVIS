# jarvis/hud/execution_log_widget.py
#
# Widget de log de execução para tarefas complexas
# Mostra etapas do Agent em tempo real

import tkinter as tk
from jarvis.hud.theme import *

class ExecutionLogWidget:
    """
    Widget que aparece durante execução de tarefas complexas.
    Mostra o progresso das etapas em tempo real.
    """

    def __init__(self, canvas, root, x=50, y=100, width=400):
        self.canvas = canvas
        self.root = root
        self.x = x
        self.y = y
        self.width = width
        self.height = 200
        self._steps = []
        self._visible = False
        self._items = []  # IDs dos elementos canvas

    def show(self, task_name: str):
        """
        Exibe o painel de log com o nome da tarefa.
        """
        if self._visible:
            self.hide()

        self._visible = True
        self._steps = []

        # Fundo semi-transparente
        self._items.append(self.canvas.create_rectangle(
            self.x, self.y, self.x + self.width, self.y + self.height,
            fill=FUNDO_TRANSPARENTE, outline=AZUL_PRIMARIO, width=2
        ))

        # Título
        title = f"[ EXECUTANDO: {task_name[:30]} ]"
        self._items.append(self.canvas.create_text(
            self.x + 10, self.y + 15, text=title,
            fill=BRANCO_TEXTO, font=("Courier", 10, "bold"), anchor="w"
        ))

        # Linha separadora
        self._items.append(self.canvas.create_line(
            self.x + 5, self.y + 30, self.x + self.width - 5, self.y + 30,
            fill=AZUL_PRIMARIO, width=1
        ))

    def add_step(self, step_num: int, tool_name: str, status: str = "running"):
        """
        Adiciona uma nova etapa ao log.

        Args:
            step_num: Número da etapa
            tool_name: Nome da ferramenta sendo executada
            status: "running", "done", "error"
        """
        if not self._visible:
            return

        # Determinar ícone baseado no status
        icons = {
            "running": "⏳",
            "done": "✅",
            "error": "❌"
        }
        icon = icons.get(status, "?")

        # Texto da etapa
        step_text = f"{icon} Etapa {step_num}: {tool_name}"

        # Calcular posição Y (máximo 6 linhas visíveis)
        max_visible = 6
        if len(self._steps) >= max_visible:
            # Remover linha mais antiga
            old_item = self._steps.pop(0)
            self.canvas.delete(old_item)

        y_pos = self.y + 40 + (len(self._steps) * 20)

        # Criar texto da etapa
        item_id = self.canvas.create_text(
            self.x + 10, y_pos, text=step_text,
            fill=BRANCO_TEXTO, font=("Courier", 9), anchor="w"
        )

        self._steps.append(item_id)
        self._items.append(item_id)

    def complete_step(self, step_num: int, success: bool = True):
        """
        Marca uma etapa como concluída.

        Args:
            step_num: Número da etapa
            success: True para sucesso, False para erro
        """
        if not self._visible or step_num > len(self._steps):
            return

        # Índice da etapa (step_num é 1-based, lista é 0-based)
        step_index = step_num - 1
        if step_index >= len(self._steps):
            return

        item_id = self._steps[step_index]

        # Obter texto atual
        current_text = self.canvas.itemcget(item_id, "text")

        # Atualizar ícone
        if success:
            new_text = current_text.replace("⏳", "✅")
        else:
            new_text = current_text.replace("⏳", "❌")

        self.canvas.itemconfig(item_id, text=new_text)

    def hide_after(self, seconds: int = 3):
        """
        Agenda o ocultamento do painel após N segundos.
        """
        if self._visible:
            self.root.after(seconds * 1000, self.hide)

    def hide(self):
        """
        Oculta o painel de log.
        """
        if not self._visible:
            return

        self._visible = False

        # Remover todos os itens do canvas
        for item_id in self._items:
            self.canvas.delete(item_id)

        self._items.clear()
        self._steps.clear()