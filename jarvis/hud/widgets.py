import tkinter as tk
import time
import math
import random

# Paleta de cores JARVIS
AZUL_PRIMARIO = "#00d4ff"
AZUL_ESCURO   = "#003d5c"
VERDE_OK      = "#00ff88"
AMARELO_AVISO = "#ffcc00"
VERMELHO_ERRO = "#ff4444"
BRANCO_TEXTO  = "#e0f0ff"
CINZA_TEXTO   = "#557799"
FUNDO         = "#000d1a"


class StateIndicator:
    def __init__(self, canvas: tk.Canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y
        self._pulsing = False

    def draw(self):
        # Círculo
        self.canvas.create_oval(
            self.x - 20, self.y - 20, self.x + 20, self.y + 20,
            fill=AZUL_PRIMARIO, outline=AZUL_PRIMARIO, tags="state_circle"
        )
        # Texto
        self.canvas.create_text(
            self.x, self.y + 35, text="● AGUARDANDO",
            fill=AZUL_PRIMARIO, font=("Courier", 12, "bold"), tags="state_text"
        )

    def update(self, state: str, action: str = ""):
        # Mapear estado para cor
        color_map = {
            "idle": AZUL_PRIMARIO,
            "listening": VERDE_OK,
            "thinking": AMARELO_AVISO,
            "speaking": AZUL_PRIMARIO,
            "acting": AMARELO_AVISO,
            "error": VERMELHO_ERRO
        }
        color = color_map.get(state, AZUL_PRIMARIO)
        
        # Mapear estado para texto
        text_map = {
            "idle": "● AGUARDANDO",
            "listening": "◉ OUVINDO...",
            "thinking": "◎ PROCESSANDO...",
            "speaking": "◉ FALANDO...",
            "acting": "◈ EXECUTANDO...",
            "error": "⚠ ERRO"
        }
        label = text_map.get(state, "● DESCONHECIDO")
        if action:
            label += f": {action}"
        
        # Atualizar visual
        self.canvas.itemconfig("state_circle", fill=color, outline=color)
        self.canvas.itemconfig("state_text", text=label, fill=color)
        
        # Iniciar/parar pulso
        if state != "idle" and not self._pulsing:
            self._pulsing = True
            self._pulse(state, color)
        elif state == "idle" and self._pulsing:
            self._pulsing = False

    def _pulse(self, state: str, base_color: str, step: int = 0):
        if not self._pulsing or state == "idle":
            return
        
        # Variação de opacidade simulada
        intensity = 0.8 + 0.2 * math.sin(step * 0.2)
        
        # Interpolar cor (simplificado)
        if base_color == VERDE_OK:
            r, g, b = 0, 255, 136
        elif base_color == AMARELO_AVISO:
            r, g, b = 255, 204, 0
        elif base_color == AZUL_PRIMARIO:
            r, g, b = 0, 212, 255
        elif base_color == VERMELHO_ERRO:
            r, g, b = 255, 68, 68
        else:
            r, g, b = 0, 212, 255
        
        r = int(r * intensity)
        g = int(g * intensity)
        b = int(b * intensity)
        pulse_color = f"#{r:02x}{g:02x}{b:02x}"
        
        self.canvas.itemconfig("state_circle", fill=pulse_color, outline=pulse_color)
        self.canvas.after(100, lambda: self._pulse(state, base_color, step + 1))


class ConversationPanel:
    def __init__(self, canvas: tk.Canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y

    def draw(self):
        # Retângulo de fundo
        self.canvas.create_rectangle(
            self.x, self.y, self.x + 350, self.y + 400,
            fill=AZUL_ESCURO, outline=AZUL_PRIMARIO, width=1
        )
        # Título
        self.canvas.create_text(
            self.x + 175, self.y + 15, text="[ REGISTRO DE COMUNICAÇÃO ]",
            fill=AZUL_PRIMARIO, font=("Courier", 10, "bold")
        )
        # Linhas de texto (8 linhas)
        for i in range(8):
            self.canvas.create_text(
                self.x + 10, self.y + 40 + i * 20, text="",
                fill=BRANCO_TEXTO, font=("Courier", 9), anchor="w",
                tags=f"conv_line_{i}"
            )

    def update(self, conversation_log: list):
        # Pegar últimas 8 entradas
        recent = conversation_log[-8:] if len(conversation_log) > 8 else conversation_log
        
        for i in range(8):
            if i < len(recent):
                entry = recent[i]
                role = entry["role"]
                text = entry["text"][:50] + "..." if len(entry["text"]) > 50 else entry["text"]
                time_str = entry["time"]
                
                if role == "user":
                    line = f"▶ [{time_str}] {text}"
                    color = BRANCO_TEXTO
                else:
                    line = f"◀ [{time_str}] {text}"
                    color = AZUL_PRIMARIO
            else:
                line = ""
                color = BRANCO_TEXTO
            
            self.canvas.itemconfig(f"conv_line_{i}", text=line, fill=color)


class AudioWaveform:
    def __init__(self, canvas: tk.Canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y
        self._animating = False
        self._frame = 0

    def draw(self):
        # 20 barras
        for i in range(20):
            x1 = self.x + i * 12
            y1 = self.y - 5
            x2 = x1 + 8
            y2 = self.y + 5
            self.canvas.create_rectangle(
                x1, y1, x2, y2, fill=VERDE_OK, tags=f"wave_bar_{i}"
            )

    def start_animation(self):
        if not self._animating:
            self._animating = True
            self._animate()

    def stop_animation(self):
        self._animating = False
        # Resetar barras
        for i in range(20):
            x1 = self.x + i * 12
            y1 = self.y - 5
            x2 = x1 + 8
            y2 = self.y + 5
            self.canvas.coords(f"wave_bar_{i}", x1, y1, x2, y2)

    def _animate(self):
        if not self._animating:
            return
        
        self._frame += 1
        for i in range(20):
            # Altura baseada em seno para movimento suave
            height = 5 + 35 * (math.sin(self._frame * 0.2 + i * 0.5) + 1) / 2
            x1 = self.x + i * 12
            y1 = self.y - height
            x2 = x1 + 8
            y2 = self.y + height
            self.canvas.coords(f"wave_bar_{i}", x1, y1, x2, y2)
        
        self.canvas.after(50, self._animate)


class SystemMonitor:
    def __init__(self, canvas: tk.Canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y

    def draw(self):
        # Retângulo de fundo
        self.canvas.create_rectangle(
            self.x, self.y, self.x + 200, self.y + 120,
            fill=AZUL_ESCURO, outline=AZUL_PRIMARIO, width=1
        )
        # Título
        self.canvas.create_text(
            self.x + 100, self.y + 15, text="[ DIAGNÓSTICO DO SISTEMA ]",
            fill=AZUL_PRIMARIO, font=("Courier", 9, "bold")
        )
        # Labels
        self.canvas.create_text(
            self.x + 10, self.y + 40, text="CPU: --%",
            fill=BRANCO_TEXTO, font=("Courier", 10), anchor="w", tags="sys_cpu"
        )
        self.canvas.create_text(
            self.x + 10, self.y + 60, text="RAM: --% (--GB)",
            fill=BRANCO_TEXTO, font=("Courier", 10), anchor="w", tags="sys_ram"
        )
        self.canvas.create_text(
            self.x + 10, self.y + 90, text="HORA: --:--:--",
            fill=CINZA_TEXTO, font=("Courier", 10), anchor="w", tags="sys_time"
        )

    def start_update(self):
        self.canvas.after(2000, self._update)

    def _update(self):
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            mem = psutil.virtual_memory()
            
            # Cor baseada no CPU
            if cpu_percent < 50:
                color = VERDE_OK
            elif cpu_percent < 80:
                color = AMARELO_AVISO
            else:
                color = VERMELHO_ERRO
            
            self.canvas.itemconfig("sys_cpu", text=f"CPU: {cpu_percent:.1f}%", fill=color)
            self.canvas.itemconfig("sys_ram", text=f"RAM: {mem.percent:.1f}% ({mem.used/1e9:.1f}GB)", fill=color)
            self.canvas.itemconfig("sys_time", text=time.strftime("HORA: %H:%M:%S"), fill=CINZA_TEXTO)
        except Exception as e:
            self.canvas.itemconfig("sys_cpu", text="CPU: ERRO", fill=VERMELHO_ERRO)
        
        self.canvas.after(2000, self._update)


class ToolIndicator:
    def __init__(self, canvas: tk.Canvas, x: int, y: int):
        self.canvas = canvas
        self.x = x
        self.y = y

    def draw(self):
        # Texto oculto inicialmente
        self.canvas.create_text(
            self.x, self.y, text="", fill=AMARELO_AVISO,
            font=("Courier", 14, "bold"), tags="tool_name", state="hidden"
        )
        self.canvas.create_text(
            self.x, self.y - 25, text="", fill=AMARELO_AVISO,
            font=("Courier", 20), tags="tool_icon", state="hidden"
        )

    def show(self, tool_name: str):
        # Mapear para ícone
        icon_map = {
            "open_app": "📂",
            "search_web": "🔍",
            "take_screenshot": "📸",
            "write_file": "📝",
            "read_file": "📖",
            "type_text": "⌨",
            "press_key": "🎹",
            "set_volume": "🔊",
            "search_wikipedia": "📚",
            "get_page_text": "📄",
            "list_files": "📁",
            "create_folder": "📁",
            "delete_file": "🗑",
            "read_clipboard": "📋",
            "write_clipboard": "📋"
        }
        icon = icon_map.get(tool_name, "⚙")
        
        self.canvas.itemconfig("tool_icon", text=icon, state="normal")
        self.canvas.itemconfig("tool_name", text=tool_name.replace("_", " ").title(), state="normal")
        
        # Auto-ocultar após 3 segundos
        self.canvas.after(3000, self.hide)

    def hide(self):
        self.canvas.itemconfig("tool_icon", state="hidden")
        self.canvas.itemconfig("tool_name", state="hidden")