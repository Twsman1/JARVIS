import tkinter as tk
import math
import time
import threading
import queue
import datetime

import numpy as np
import psutil

from jarvis.core import (
    _command_active,
    _shutdown,
    _vad_active,
    status_queue,
    history_queue,
    amplitude_queue,
    log,
)
from jarvis.hud.theme import *
from jarvis.hud.widgets import StateIndicator, ConversationPanel, AudioWaveform, SystemMonitor, ToolIndicator
from jarvis.hud.execution_log_widget import ExecutionLogWidget
from jarvis.hud import state
from jarvis.config import (
    SAMPLE_RATE,
    BLOCK_SIZE,
    CHANNELS,
    DTYPE,
    VAD_MAX_DURATION,
    VAD_MIN_SPEECH,
    VAD_MIN_SILENCE,
    WHISPER_MODEL,
    WAKE_WORD,
)

# window state
W, H = DEFAULT_W, DEFAULT_H
cx, cy = W // 2, H // 2
_fullscreen = False

# internal animation state
_angle = 0.0
_wave_t = 0.0
_scan_y = 0
_amp_buf = [0] * 100
_amp_smooth = 0.0
_status_log = ["Inicializando..."]
_history_log: list[str] = []
_history_ts: list[str] = []

# psutil cache
_sys_cache: dict = {}
_sys_cache_ts: float = 0.0
_sys_boot = datetime.datetime.fromtimestamp(psutil.boot_time())

# helpers for external modules
timeout_job = None

root: tk.Tk = None
canvas: tk.Canvas = None

# HUD widgets
_state_indicator = None
_conversation_panel = None
_audio_waveform = None
_system_monitor = None
_tool_indicator = None

# resizing flag
_static_drawn: bool = False
_last_wh: tuple = (0, 0)


# ---------------------------------------------------------------------------
# initialization
# ---------------------------------------------------------------------------

def init_gui():
    global root, canvas, W, H, cx, cy
    root = tk.Tk()
    root.title("J.A.R.V.I.S.")
    root.geometry(f"{W}x{H}")
    root.configure(bg="black")
    root.resizable(True, True)

    canvas = tk.Canvas(root, bg="black", highlightthickness=0, width=W, height=H)
    canvas.pack(fill="both", expand=True)

    root.bind("<F11>", _toggle_fullscreen)
    canvas.bind("<Configure>", _on_resize)
    root.bind("<Escape>", _exit_fullscreen)

    return root, canvas


def _toggle_fullscreen(event=None):
    global _fullscreen, W, H, cx, cy, _static_drawn
    _fullscreen = not _fullscreen
    root.attributes("-fullscreen", _fullscreen)
    if _fullscreen:
        root.update_idletasks()
        W = root.winfo_width()
        H = root.winfo_height()
    else:
        W, H = DEFAULT_W, DEFAULT_H
        root.geometry(f"{W}x{H}")
        root.update_idletasks()
    cx, cy = W // 2, H // 2
    canvas.config(width=W, height=H)
    _static_drawn = False


def _on_resize(event):
    global W, H, cx, cy, _static_drawn
    if event.width != W or event.height != H:
        W, H = event.width, event.height
        cx, cy = W // 2, H // 2
        canvas.config(width=W, height=H)
        _static_drawn = False


def _exit_fullscreen(event=None):
    global _fullscreen, W, H, cx, cy, _static_drawn
    if _fullscreen:
        _fullscreen = False
        root.attributes("-fullscreen", False)
        W, H = DEFAULT_W, DEFAULT_H
        cx, cy = W // 2, H // 2
        root.geometry(f"{W}x{H}")
        canvas.config(width=W, height=H)
        _static_drawn = False

# ---------------------------------------------------------------------------
# state management
# ---------------------------------------------------------------------------

def _drain():
    global _amp_smooth
    # Amplitude
    latest_rms = 0
    try:
        while True:
            v = amplitude_queue.get_nowait()
            _amp_buf.append(v)
            _amp_buf.pop(0)
            latest_rms = v
    except queue.Empty:
        pass
    alpha = 0.4 if _command_active.is_set() else 0.15
    _amp_smooth = _amp_smooth * (1 - alpha) + (latest_rms / 3000.0) * alpha
    _amp_smooth = max(0.0, min(1.0, _amp_smooth))

    # Status
    try:
        while True:
            _status_log.append(status_queue.get_nowait())
            if len(_status_log) > 30:
                _status_log.pop(0)
    except queue.Empty:
        pass
    # History
    try:
        while True:
            cmd = history_queue.get_nowait()
            _history_log.append(cmd)
            _history_ts.append(datetime.datetime.now().strftime("%H:%M:%S"))
    except queue.Empty:
        pass


def _pulse(spd=3.0, lo=0.0, hi=1.0):
    return lo + (hi - lo) * (0.5 + 0.5 * math.sin(time.time() * spd))

# system metrics

def _get_sys_metrics() -> dict:
    global _sys_cache, _sys_cache_ts
    now = time.time()
    if now - _sys_cache_ts < 1.0:
        return _sys_cache

    cpu = psutil.cpu_percent(interval=None)
    mem = psutil.virtual_memory()
    ram = mem.percent
    try:
        disk = psutil.disk_usage("/").percent
    except Exception:
        disk = 0.0
    temp = None
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for key in ("coretemp", "cpu_thermal", "k10temp", "acpitz"):
                if key in temps and temps[key]:
                    temp = temps[key][0].current
                    break
            if temp is None:
                temp = list(temps.values())[0][0].current
    except Exception:
        temp = None
    procs = len(psutil.pids())
    uptime = datetime.datetime.now() - _sys_boot
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, s = divmod(rem, 60)
    uptime_str = f"{h:02d}:{m:02d}:{s:02d}"

    _sys_cache = {
        "cpu": cpu,
        "ram": ram,
        "disk": disk,
        "temp": temp,
        "procs": procs,
        "uptime": uptime_str,
    }
    _sys_cache_ts = now
    return _sys_cache


def _warmup_psutil():
    psutil.cpu_percent(interval=1)
threading.Thread(target=_warmup_psutil, daemon=True, name="psutil-warmup").start()

# ---------------------------------------------------------------------------
# drawing logic (most of original hud code)
# ---------------------------------------------------------------------------

def _draw_static_layer():
    canvas.delete("static")
    for x in range(0, W, 30):
        canvas.create_line(x, 0, x, H, fill=HUD_GRID, tags="static")
    for y in range(0, H, 30):
        canvas.create_line(0, y, W, y, fill=HUD_GRID, tags="static")
    _draw_left_panel()
    _draw_right_panel_static()
    _draw_top_bar()


def draw_hud():
    global _angle, _wave_t, _scan_y, _static_drawn, _last_wh
    _drain()
    current_wh = (W, H)
    if not _static_drawn or current_wh != _last_wh:
        _draw_static_layer()
        _static_drawn = True
        _last_wh = current_wh
    canvas.delete("dynamic")
    # Scan line
    canvas.create_line(0, _scan_y, W, _scan_y, fill="#001C28", tags="dynamic")

    # Rings  — raios expandem proporcionalmente à amplitude real do microfone
    amp = _amp_smooth
    ring_expand = amp * 30
    def _ring_color(base_expand):
        intensity = min(1.0, amp * 2.5)
        r = int(0x00 + intensity * 0x00)
        g = int(0x4D + intensity * (0xF5 - 0x4D))
        b = int(0x5C + intensity * (0xFF - 0x5C))
        return f"#{r:02X}{g:02X}{b:02X}"
    ring_specs = [
        (310, 1, HUD_GRID,  0.0),
        (280, 1, HUD_DIM,   0.3),
        (250, 2, HUD_MID,   0.6),
        (215, 1, HUD_DIM,   0.8),
        (180, 2, HUD_BLUE,  1.0),
    ]
    for rb, w, col_base, factor in ring_specs:
        r = rb + int(ring_expand * factor)
        col = _ring_color(factor) if factor >= 0.6 and amp > 0.05 else col_base
        lw  = w + (1 if amp > 0.3 and factor >= 0.6 else 0)
        canvas.create_oval(cx-r, cy-r, cx+r, cy+r, outline=col, width=lw, tags="dynamic")
    ae = int(amp * 20)
    a1 = _angle % 360
    canvas.create_arc(cx-(310+ae),cy-(310+ae),cx+(310+ae),cy+(310+ae), start=a1, extent=100,
                      style="arc", outline=HUD_CYAN, width=3, tags="dynamic")
    canvas.create_arc(cx-(310+ae),cy-(310+ae),cx+(310+ae),cy+(310+ae), start=a1+180, extent=50,
                      style="arc", outline=HUD_BLUE, width=2, tags="dynamic")
    a2 = (-_angle*1.4) % 360
    canvas.create_arc(cx-(250+ae//2),cy-(250+ae//2),cx+(250+ae//2),cy+(250+ae//2), start=a2, extent=80,
                      style="arc", outline="#00CCDD", width=2, tags="dynamic")
    a3 = (_angle*2.8) % 360
    canvas.create_arc(cx-180,cy-180,cx+180,cy+180, start=a3, extent=160,
                      style="arc", outline=HUD_CYAN, width=2, tags="dynamic")
    bx = cx + (215+ae)*math.cos(math.radians(_angle))
    by = cy + (215+ae)*math.sin(math.radians(_angle))
    canvas.create_line(cx, cy, bx, by, fill=HUD_CYAN, width=2, tags="dynamic")
    for i in range(14):
        a  = math.radians(_angle*1.1 + i*25.7)
        r  = 155 + 10*math.sin(time.time()*2+i)
        px = cx + r*math.cos(a); py = cy + r*math.sin(a)
        s  = 2 + (i%3)
        canvas.create_oval(px-s,py-s,px+s,py+s,
                           fill=HUD_CYAN if i%2==0 else HUD_BLUE, outline="", tags="dynamic")
    p   = _pulse(4, 38, 58)
    col = HUD_ACCENT if _command_active.is_set() else HUD_CYAN
    canvas.create_oval(cx-p-15, cy-p-15, cx+p+15, cy+p+15,
                       fill="", outline=HUD_MID, width=2, tags="dynamic")
    canvas.create_oval(cx-p, cy-p, cx+p, cy+p, fill=col, outline="", tags="dynamic")
    inner = p*0.45
    canvas.create_oval(cx-inner,cy-inner,cx+inner,cy+inner, fill="white", outline="", tags="dynamic")
    for ang, ll in [(0,290),(90,290),(45,120),(135,120)]:
        r2 = math.radians(ang)
        canvas.create_line(cx+65*math.cos(r2),cy+65*math.sin(r2),
                           cx+ll*math.cos(r2), cy+ll*math.sin(r2),
                           fill=HUD_DIM, dash=(5,8), tags="dynamic")
    if _vad_active.is_set():
        gp = _pulse(8, 5, 12)
        canvas.create_oval(cx-gp,cy-gp,cx+gp,cy+gp,
                           fill="", outline=HUD_ACCENT, width=3, tags="dynamic")
    for i in range(0, 360, 5):
        rad = math.radians(i)
        ir  = 207 if i%30==0 else (210 if i%10==0 else 212)
        x1 = cx+ir*math.cos(rad); y1 = cy+ir*math.sin(rad)
        x2 = cx+218*math.cos(rad); y2 = cy+218*math.sin(rad)
        col2 = HUD_CYAN if i%90==0 else (HUD_MID if i%30==0 else HUD_DIM)
        canvas.create_line(x1,y1,x2,y2, fill=col2, width=2 if i%90==0 else 1, tags="dynamic")
    for deg, lbl in [(0,"E"),(90,"S"),(180,"W"),(270,"N")]:
        r3 = math.radians(deg)
        canvas.create_text(cx+238*math.cos(r3), cy+238*math.sin(r3),
                           text=lbl, fill=HUD_CYAN, font=("Courier",9,"bold"), tags="dynamic")
    _draw_right_panel_dynamic()
    _draw_bottom_bar()
    _draw_live_waveform()

    # Initialize widgets if not done yet
    global _state_indicator, _conversation_panel, _audio_waveform, _system_monitor, _tool_indicator, _execution_log
    if _state_indicator is None:
        _state_indicator = StateIndicator(canvas, cx, 40)
        _state_indicator.draw()
        
        _conversation_panel = ConversationPanel(canvas, 20, 80)
        _conversation_panel.draw()
        
        _audio_waveform = AudioWaveform(canvas, cx - 120, H - 80)
        _audio_waveform.draw()
        
        _system_monitor = SystemMonitor(canvas, W - 250, 80)
        _system_monitor.draw()
        _system_monitor.start_update()
        
        _tool_indicator = ToolIndicator(canvas, cx, H - 120)
        _tool_indicator.draw()
        
        _execution_log = ExecutionLogWidget(canvas, root, 50, 100)
        
        # Register observer
        state.register_observer(_on_state_change)

    _angle  += 2.2
    _wave_t += 0.14
    _scan_y  = (_scan_y + 3) % H
    root.after(30, draw_hud)


def _on_state_change(new_state, action):
    """Callback when state changes - must use root.after for thread safety"""
    root.after(0, lambda: _state_indicator.update(new_state, action))
    root.after(0, lambda: _conversation_panel.update(state.get_conversation_log()))
    if new_state == "listening":
        root.after(0, _audio_waveform.start_animation)
    else:
        root.after(0, _audio_waveform.stop_animation)
    if new_state == "acting":
        root.after(0, lambda: _tool_indicator.show(action))


def _draw_left_panel():
    x0, y0, pw = 15, 100, 225
    canvas.create_rectangle(x0, y0, x0+pw, y0+490,
                             outline=HUD_MID, width=1, dash=(4,5), tags="static")
    canvas.create_text(x0+8, y0+10, text="SYSTEM STATUS",
                       fill=HUD_CYAN, font=("Courier",10,"bold"), anchor="w", tags="static")

    m   = _get_sys_metrics()
    cpu  = m["cpu"]
    ram  = m["ram"]
    disk = m["disk"]
    temp = m["temp"]
    procs= m["procs"]

    def _metric_color(pct: float) -> str:
        if pct >= 85: return HUD_ACCENT
        if pct >= 60: return HUD_YELLOW
        return HUD_CYAN

    temp_str = f"{temp:.0f}C" if temp is not None else "N/A"
    temp_col = HUD_ACCENT if (temp or 0) >= 80 else (
               HUD_YELLOW if (temp or 0) >= 65 else HUD_GREEN)

    rows = [
        ("UPTIME",   m["uptime"],          HUD_GREEN,              None),
        ("CPU",      f"{cpu:.0f}%",        _metric_color(cpu),     cpu/100),
        ("RAM",      f"{ram:.0f}%",        _metric_color(ram),     ram/100),
        ("DISCO",    f"{disk:.0f}%",       _metric_color(disk),    disk/100),
        ("TEMP",     temp_str,             temp_col,               min((temp or 0)/100, 1.0)),
        ("PROC",     str(procs),           HUD_CYAN,               min(procs/300, 1.0)),
        ("NETWORK",  "ONLINE",             HUD_GREEN,              None),
        ("ASR",      "WHISPER/PT",         HUD_GREEN,              None),
        ("VOICE",    "CMD" if _command_active.is_set() else "LISTEN",
                     HUD_ACCENT if _command_active.is_set() else HUD_GREEN, None),
        ("VAD",      "SPEECH" if _vad_active.is_set() else "SILENCE",
                     HUD_ACCENT if _vad_active.is_set() else HUD_DIM,      None),
    ]
    bw = int(pw * 0.72)
    for i, (k, v, col, pct) in enumerate(rows):
        yy = y0 + 32 + i * 44
        canvas.create_text(x0+12, yy,    text=k, fill=HUD_DIM,
                           font=("Courier",8), anchor="w")
        canvas.create_text(x0+12, yy+13, text=v, fill=col,
                           font=("Courier",11,"bold"), anchor="w")
        if pct is not None:
            canvas.create_rectangle(x0+12, yy+26, x0+12+bw, yy+32,
                                     fill="#001820", outline="")
            canvas.create_rectangle(x0+12, yy+26, x0+12+int(bw*pct), yy+32,
                                     fill=col, outline="")


def _draw_right_panel_static():
    x0, y0, pw = W-240, 100, 225
    canvas.create_rectangle(x0, y0, x0+pw, y0+490,
                             outline=HUD_MID, width=1, dash=(4,5), tags="static")
    canvas.create_text(x0+8, y0+10, text="ANALYTICS",
                       fill=HUD_CYAN, font=("Courier",10,"bold"), anchor="w", tags="static")
    canvas.create_text(x0+8, y0+128, text="SIGNAL SPECTRUM",
                       fill=HUD_DIM, font=("Courier",7), anchor="w", tags="static")
    canvas.create_text(x0+8, y0+272, text="RADAR TRACKING",
                       fill=HUD_DIM, font=("Courier",7), anchor="w", tags="static")
    canvas.create_text(x0+8, y0+285, text="MIC AMPLITUDE",
                       fill=HUD_DIM, font=("Courier",7), anchor="w", tags="static")
    canvas.create_rectangle(x0+8, y0+315, x0+pw-8, y0+490,
                             fill="#000810", outline=HUD_DIM, width=1, tags="static")
    canvas.create_text(x0+12, y0+322, text="CMD LOG",
                       fill=HUD_CYAN, font=("Courier",8,"bold"), anchor="w", tags="static")
    canvas.create_line(x0+8, y0+332, x0+pw-8, y0+332, fill=HUD_DIM, tags="static")


def _draw_right_panel_dynamic():
    x0, y0, pw = W-240, 100, 225

    for i in range(10):
        base = abs(math.sin(time.time()*0.5+i*0.72))
        reactive = _amp_smooth * abs(math.sin(time.time()*3+i*1.3))
        bh  = int(15 + (base*50 + reactive*50))
        bx  = x0+12+i*19
        col = HUD_ACCENT if i%3==0 else (HUD_CYAN if _amp_smooth < 0.3 else "#00FFCC")
        canvas.create_rectangle(bx, y0+120-bh, bx+17, y0+120, fill=col, outline="", tags="dynamic")

    rcx, rcy, rr = x0+112, y0+210, 50
    canvas.create_oval(rcx-rr,rcy-rr,rcx+rr,rcy+rr, outline=HUD_MID, tags="dynamic")
    canvas.create_oval(rcx-rr//2,rcy-rr//2,rcx+rr//2,rcy+rr//2, outline=HUD_DIM, tags="dynamic")
    ra = math.radians(_angle*1.9)
    canvas.create_line(rcx, rcy, rcx+rr*math.cos(ra), rcy+rr*math.sin(ra),
                       fill=HUD_CYAN, width=2, tags="dynamic")
    bx2 = rcx+int(rr*0.6*math.cos(math.radians(137)))
    by2 = rcy+int(rr*0.6*math.sin(math.radians(137)))
    bp  = _pulse(2.1, 2, 5)
    canvas.create_oval(bx2-bp,by2-bp,bx2+bp,by2+bp, fill=HUD_ACCENT, outline="", tags="dynamic")

    amp_bw = pw - 20
    canvas.create_rectangle(x0+10, y0+295, x0+10+amp_bw, y0+305,
                             fill="#001820", outline=HUD_DIM, tags="dynamic")
    amp_fill = int(amp_bw * _amp_smooth)
    amp_col  = HUD_ACCENT if _amp_smooth > 0.6 else (HUD_YELLOW if _amp_smooth > 0.3 else HUD_CYAN)
    if amp_fill > 0:
        canvas.create_rectangle(x0+10, y0+295, x0+10+amp_fill, y0+305,
                                 fill=amp_col, outline="", tags="dynamic")
    canvas.create_text(x0+10+amp_bw-2, y0+300,
                       text=f"{int(_amp_smooth*100)}%",
                       fill=HUD_DIM, font=("Courier",7), anchor="e", tags="dynamic")

    entries = list(zip(_history_log, _history_ts))[-5:]
    entries.reverse()
    for i, (cmd, ts) in enumerate(entries):
        yy     = y0 + 340 + i * 28
        canvas.create_text(x0+12, yy, text=f"[{ts}]",
                           fill=HUD_DIM, font=("Courier",7), anchor="w", tags="dynamic")
        display = cmd[:28] + "..." if len(cmd) > 28 else cmd
        col_cmd = HUD_GREEN if i == 0 else HUD_MID
        canvas.create_text(x0+12, yy+13, text="> " + display,
                           fill=col_cmd, font=("Courier",8,"bold"), anchor="w", tags="dynamic")

    if not _history_log:
        canvas.create_text(x0+12, y0+355, text="aguardando comandos...",
                           fill=HUD_DIM, font=("Courier",8,"italic"), anchor="w", tags="dynamic")


def _draw_top_bar():
    canvas.create_rectangle(0, 0, W, 95, fill=HUD_BG, outline="", tags="static")
    canvas.create_line(0, 95, W, 95, fill=HUD_MID, width=1, tags="static")
    for ox in (360, W-360):
        canvas.create_line(ox, 4, ox, 91, fill=HUD_DIM, width=1, tags="static")
    canvas.create_text(cx, 32, text="J.A.R.V.I.S.",
                       fill=HUD_CYAN, font=("Courier",28,"bold"), anchor="center", tags="static")
    canvas.create_text(cx, 60,
                       text="JUST A RATHER VERY INTELLIGENT SYSTEM  |  STARK INDUSTRIES",
                       fill=HUD_MID, font=("Courier",9), anchor="center", tags="static")
    canvas.create_text(cx, 76,
                       text=f"ASR: faster-whisper [{WHISPER_MODEL.upper()}]  |  LANG: PT-BR  |  VAD: SILERO",
                       fill=HUD_DIM, font=("Courier",8), anchor="center", tags="static")
    canvas.create_text(12, 16, text="BUILD 4.7.2",        fill=HUD_DIM, font=("Courier",8), anchor="w", tags="static")
    canvas.create_text(12, 30, text="VOSK + WHISPER",     fill=HUD_DIM, font=("Courier",8), anchor="w", tags="static")
    canvas.create_text(12, 44, text="PT-BR ENGINE",       fill=HUD_DIM, font=("Courier",8), anchor="w", tags="static")
    canvas.create_text(W-12, 16, text="SECURE MODE",            fill=HUD_DIM, font=("Courier",8), anchor="e", tags="static")
    canvas.create_text(W-12, 30, text="LOCAL PROCESSING",       fill=HUD_DIM, font=("Courier",8), anchor="e", tags="static")
    canvas.create_text(W-12, 44, text="OFFLINE ASR ENGINE",     fill=HUD_DIM, font=("Courier",8), anchor="e", tags="static")
    fs_hint = "[ESC] JANELA" if _fullscreen else "[F11] CINEMA"
    canvas.create_text(W-12, 76, text=fs_hint, fill=HUD_MID, font=("Courier",8), anchor="e", tags="static")


def _draw_bottom_bar():
    y0 = H - 65
    canvas.create_rectangle(0, y0, W, H, fill=HUD_BG, outline="", tags="dynamic")
    canvas.create_line(0, y0, W, y0, fill=HUD_MID, width=1, tags="dynamic")
    status = _status_log[-1] if _status_log else "..."
    canvas.create_text(cx, y0+14, text=status,
                       fill=HUD_CYAN, font=("Courier",12,"bold"), anchor="center", tags="dynamic")
    mode_col = HUD_ACCENT if _command_active.is_set() else HUD_GREEN
    mode_txt = "COMANDO ATIVO" if _command_active.is_set() \
               else ("SPEECH DETECTED" if _vad_active.is_set() else "LISTENING: "+WAKE_WORD.upper())
    canvas.create_oval(12, y0+30, 24, y0+42, fill=mode_col, outline="", tags="dynamic")
    canvas.create_text(30, y0+36, text=mode_txt, fill=mode_col,
                       font=("Courier",9), anchor="w", tags="dynamic")
    ts = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    canvas.create_text(W-12, y0+10, text=ts, fill=HUD_DIM,
                       font=("Courier",9), anchor="e", tags="dynamic")
    canvas.create_text(W-12, y0+24, text="LAT 23.5505S  LON 46.6333W",
                       fill=HUD_DIM, font=("Courier",8), anchor="e", tags="dynamic")
    # note: whisper_asr imported later in main to avoid dependency loop
    from jarvis.voice.transcriber import whisper_asr
    w_col = HUD_GREEN if whisper_asr.ready else HUD_YELLOW
    w_txt = f"WHISPER [{WHISPER_MODEL.upper()}] READY" if whisper_asr.ready \
            else f"WHISPER [{WHISPER_MODEL.upper()}] LOADING..."
    canvas.create_text(cx, y0+46, text=w_txt, fill=w_col,
                       font=("Courier",8), anchor="center", tags="dynamic")


def _draw_live_waveform():
    y0 = H - 63
    if len(_amp_buf) < 4:
        return
    pts = []
    for i, amp in enumerate(_amp_buf):
        x = int(i * W / len(_amp_buf))
        scale = 20 if _command_active.is_set() else 7
        y = y0 - int(amp / 3000 * scale)
        pts.extend([x, y])
    if len(pts) >= 4:
        col = HUD_ACCENT if _command_active.is_set() else HUD_MID
        canvas.create_line(*pts, fill=col, width=1, smooth=True, tags="dynamic")


# loading overlay
_LOADING_TAG = "loading_overlay"

def _draw_loading_overlay():
    whisper_ok = False
    vad_ok = False
    try:
        from jarvis.voice.transcriber import whisper_asr
        whisper_ok = whisper_asr.ready
    except Exception:
        pass
    from jarvis.voice.vad import vad
    vad_ok = vad.ready

    canvas.delete(_LOADING_TAG)

    if whisper_ok and vad_ok:
        log.info("Todos os sistemas prontos — overlay removido.")
        return

    canvas.create_rectangle(
        cx - 320, cy - 110, cx + 320, cy + 110,
        fill=HUD_BG, outline=HUD_MID, width=2,
        tags=_LOADING_TAG,
    )
    canvas.create_rectangle(
        cx - 315, cy - 105, cx + 315, cy + 105,
        fill="", outline=HUD_DIM, width=1, dash=(6, 4),
        tags=_LOADING_TAG,
    )
    canvas.create_text(
        cx, cy - 75,
        text="⬡  J.A.R.V.I.S.  ⬡",
        fill=HUD_CYAN, font=("Courier", 15, "bold"), anchor="center",
        tags=_LOADING_TAG,
    )
    canvas.create_text(
        cx, cy - 50,
        text="INICIALIZANDO SISTEMAS — AGUARDE",
        fill=HUD_MID, font=("Courier", 9), anchor="center",
        tags=_LOADING_TAG,
    )

    def _status_line(label: str, ready: bool, y_offset: int):
        dot_col  = HUD_GREEN  if ready else HUD_YELLOW
        dot_text = "●  PRONTO " if ready else "◌  CARREGANDO..."
        txt_col  = HUD_GREEN  if ready else HUD_YELLOW
        canvas.create_text(
            cx - 150, cy + y_offset,
            text=f"[ {label} ]", fill=HUD_DIM,
            font=("Courier", 9, "bold"), anchor="w",
            tags=_LOADING_TAG,
        )
        canvas.create_text(
            cx - 20, cy + y_offset,
            text=dot_text, fill=txt_col,
            font=("Courier", 9), anchor="w",
            tags=_LOADING_TAG,
        )

    _status_line("WHISPER ASR", whisper_ok,  -15)
    _status_line("SILERO  VAD", vad_ok,       15)

    bar_w  = 400
    fill_w = int(bar_w * (0.5 + 0.5 * math.sin(time.time() * 3)))
    canvas.create_rectangle(
        cx - bar_w//2, cy + 55, cx + bar_w//2, cy + 65,
        fill="#001820", outline=HUD_DIM, tags=_LOADING_TAG,
    )
    canvas.create_rectangle(
        cx - bar_w//2, cy + 55, cx - bar_w//2 + fill_w, cy + 65,
        fill=HUD_CYAN, outline="", tags=_LOADING_TAG,
    )
    canvas.create_text(
        cx, cy + 85,
        text="[ESC] ou [F11] disponíveis enquanto carrega",
        fill=HUD_DIM, font=("Courier", 7), anchor="center",
        tags=_LOADING_TAG,
    )

    root.after(100, _draw_loading_overlay)


