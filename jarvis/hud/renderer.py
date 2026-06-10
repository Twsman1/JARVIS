import tkinter as tk
import math
import time
import threading
import queue
import datetime
import os

import numpy as np
import psutil
import socket

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

# network/process caches
_net_cache: dict = {}
_net_cache_ts: float = 0.0
_net_last = None
_proc_cache: list[dict] = []
_proc_cache_ts: float = 0.0

# core orb cache (avoid reallocating each frame)
_orb_angles_60 = [math.radians(i * 6) for i in range(60)]
_orb_angles_120 = [math.radians(i * 3) for i in range(120)]
_orb_angles_96 = [2 * math.pi * (i / 96) for i in range(97)]

# helpers for external modules
timeout_job = None

root: tk.Tk = None
canvas: tk.Canvas = None

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
        disk_root = os.environ.get("SystemDrive", "C:") + "\\"
        disk = psutil.disk_usage(disk_root).percent
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

# network metrics
def _get_net_metrics() -> dict:
    global _net_cache, _net_cache_ts, _net_last
    now = time.time()
    if now - _net_cache_ts < 1.0 and _net_cache:
        return _net_cache

    try:
        io = psutil.net_io_counters()
    except Exception:
        io = None

    down_bps = up_bps = 0.0
    if io is not None:
        if _net_last is None:
            _net_last = (now, io.bytes_recv, io.bytes_sent)
        else:
            t0, r0, s0 = _net_last
            dt = max(0.2, now - t0)
            down_bps = max(0.0, (io.bytes_recv - r0) / dt)
            up_bps = max(0.0, (io.bytes_sent - s0) / dt)
            _net_last = (now, io.bytes_recv, io.bytes_sent)

    ip = "N/A"
    try:
        addrs = psutil.net_if_addrs()
        for ifname, lst in addrs.items():
            for a in lst:
                fam = getattr(a, "family", None)
                if fam == socket.AF_INET or int(getattr(fam, "value", fam or -1)) == int(socket.AF_INET):
                    if a.address and not a.address.startswith("127."):
                        ip = a.address
                        raise StopIteration
    except StopIteration:
        pass
    except Exception:
        pass

    _net_cache = {
        "down_bps": down_bps,
        "up_bps": up_bps,
        "ip": ip,
    }
    _net_cache_ts = now
    return _net_cache


def _get_top_processes() -> list[dict]:
    """Return top processes by CPU (cached)."""
    global _proc_cache, _proc_cache_ts
    now = time.time()
    if now - _proc_cache_ts < 3.0 and _proc_cache:
        return _proc_cache

    procs: list[dict] = []
    try:
        for p in psutil.process_iter(["name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                name = (info.get("name") or "").strip() or "process"
                cpu = float(info.get("cpu_percent") or 0.0)
                mem = float(info.get("memory_percent") or 0.0)
                procs.append({"name": name, "cpu": cpu, "mem": mem})
            except Exception:
                continue
        procs.sort(key=lambda x: (x["cpu"], x["mem"]), reverse=True)
        procs = procs[:6]
    except Exception:
        procs = []

    _proc_cache = procs
    _proc_cache_ts = now
    return _proc_cache


def _fmt_rate(bps: float) -> str:
    if bps < 1024:
        return f"{bps:.0f} B/s"
    if bps < 1024 * 1024:
        return f"{bps/1024:.1f} KB/s"
    return f"{bps/1024/1024:.1f} MB/s"

def _clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else (1.0 if x > 1.0 else x)


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02X}{g:02X}{b:02X}"


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _lerp_color(c1: str, c2: str, t: float) -> str:
    t = _clamp01(t)
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex((int(_lerp(r1, r2, t)), int(_lerp(g1, g2, t)), int(_lerp(b1, b2, t))))


def _shade(col: str, mult: float) -> str:
    r, g, b = _hex_to_rgb(col)
    return _rgb_to_hex((int(r * mult), int(g * mult), int(b * mult)))

# ---------------------------------------------------------------------------
# drawing logic (most of original hud code)
# ---------------------------------------------------------------------------

def _draw_static_layer():
    canvas.delete("static")
    for x in range(0, W, 30):
        canvas.create_line(x, 0, x, H, fill=HUD_GRID, tags="static")
    for y in range(0, H, 30):
        canvas.create_line(0, y, W, y, fill=HUD_GRID, tags="static")
    _draw_top_bar()
    _draw_left_column_static()
    _draw_right_column_static()
    _draw_center_frames_static()


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

    # Central core (reference-style orb), still reactive to mic amplitude
    amp = _amp_smooth
    _draw_core_orb(amp)
    _draw_left_column_dynamic()
    _draw_right_column_dynamic()
    _draw_bottom_bar()
    _draw_live_waveform()

    _angle  += 2.2
    _wave_t += 0.14
    _scan_y  = (_scan_y + 3) % H
    root.after(30, draw_hud)


def _draw_core_orb(amp: float):
    """Draw the central 'Jarvis-like' orb matching the reference image."""
    # scale to window size (keeps responsive)
    base = min(W, H)
    outer_r = int(base * 0.19)
    mid_r = int(outer_r * 0.78)
    inner_r = int(outer_r * 0.42)

    # audio-reactive deltas
    glow = int(amp * max(10, outer_r * 0.10))
    ae = int(amp * max(6, outer_r * 0.08))

    t = time.time()
    a1 = _angle % 360
    a0 = (_angle * 0.25) % 360

    # ------------------------------------------------------------
    # Background gradient bloom (fake radial gradient via layers)
    # ------------------------------------------------------------
    grad_outer = outer_r + 26 + glow
    for i in range(10):
        tt = i / 9.0
        rr = int(_lerp(grad_outer, outer_r - 12, tt))
        col = _lerp_color("#00141A", HUD_CYAN, (1 - tt) * 0.28 + amp * 0.22)
        col = _shade(col, 0.55 + 0.35 * (1 - tt))
        canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=col, width=2, tags="dynamic")

    # --- outer bezel (dark ring + subtle glow) ---
    # "shadow" layers
    for k, col in [(18, "#000305"), (12, "#000608"), (8, "#000A0E")]:
        r = outer_r + k
        canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=col, width=6, tags="dynamic")

    # bezel body
    r = outer_r + 6
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#0B1216", width=16, tags="dynamic")
    r = outer_r + 2
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#1A2A33", width=6, tags="dynamic")

    # cyan rim glow (intensity from amp)
    rim_col = HUD_CYAN if amp < 0.45 else "#5CFFFF"
    for k in range(3):
        rr = outer_r - 2 + k * 2 + glow
        canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=rim_col, width=2, tags="dynamic")

    # tick marks / segmented ring (high detail but lightweight)
    tick_r1 = outer_r - 8
    tick_r2 = outer_r - 20
    for i, ang in enumerate(_orb_angles_120):
        # alternate tick lengths
        major = (i % 10 == 0)
        r1 = tick_r1
        r2 = tick_r2 - (10 if major else 0)
        col = HUD_CYAN if major else HUD_DIM
        w = 2 if major else 1
        x1 = cx + r1 * math.cos(ang)
        y1 = cy + r1 * math.sin(ang)
        x2 = cx + r2 * math.cos(ang)
        y2 = cy + r2 * math.sin(ang)
        canvas.create_line(x1, y1, x2, y2, fill=col, width=w, tags="dynamic")

    # subtle "mechanical" segment ring (dashed arcs)
    seg_r = outer_r - 28
    for i in range(12):
        start = (a1 * 0.9 + i * 30) % 360
        extent = 14 + (i % 3) * 2
        col = HUD_MID if i % 2 else HUD_DIM
        canvas.create_arc(cx - seg_r, cy - seg_r, cx + seg_r, cy + seg_r, start=start, extent=extent,
                          style="arc", outline=col, width=3, tags="dynamic")

    # menu-ish labels around the rim (Tk text cannot rotate; place around circle)
    labels = ["Email", "Settings", "Custom", "None", "Network", "News", "Gaming", "Home"]
    text_r = outer_r - 10
    for i, s in enumerate(labels):
        ang = math.radians(a0 + i * (360 / len(labels)))
        tx = cx + text_r * math.cos(ang)
        ty = cy + text_r * math.sin(ang)
        canvas.create_text(tx, ty, text=s, fill=HUD_MID, font=("Courier", 8, "bold"), tags="dynamic")

    # --- inner energetic rings ---
    # outer aqua ring
    rr = mid_r + ae
    canvas.create_oval(cx - rr, cy - rr, cx + rr, cy + rr, outline=HUD_CYAN, width=5, tags="dynamic")
    canvas.create_oval(cx - (rr - 12), cy - (rr - 12), cx + (rr - 12), cy + (rr - 12), outline=HUD_DIM, width=2, tags="dynamic")

    # rotating arcs
    canvas.create_arc(cx - (rr + 10), cy - (rr + 10), cx + (rr + 10), cy + (rr + 10), start=a1, extent=120,
                      style="arc", outline=HUD_CYAN, width=5, tags="dynamic")
    canvas.create_arc(cx - (rr + 10), cy - (rr + 10), cx + (rr + 10), cy + (rr + 10), start=a1 + 170, extent=60,
                      style="arc", outline=HUD_BLUE, width=3, tags="dynamic")
    canvas.create_arc(cx - (rr - 18), cy - (rr - 18), cx + (rr - 18), cy + (rr - 18), start=(-_angle * 1.3) % 360, extent=90,
                      style="arc", outline="#00CCDD", width=3, tags="dynamic")

    # wavy plasma ring (polyline around circle)
    wav_r = int(mid_r * 0.95) + ae
    pts: list[int] = []
    wave_amp = 10 + 20 * amp
    for ang in _orb_angles_96:
        wobble = (math.sin(t * 2.2 + ang * 3.0) + 0.6 * math.sin(t * 3.1 + ang * 7.0)) * 0.5
        rad = wav_r + wobble * wave_amp
        pts.extend([int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))])
    canvas.create_line(*pts, fill=HUD_CYAN, width=3, smooth=True, splinesteps=12, tags="dynamic")
    canvas.create_line(*pts, fill="#66FFFF" if amp > 0.35 else HUD_MID, width=1, smooth=True, splinesteps=12, tags="dynamic")

    # secondary plasma ring (phase-shifted) for more depth
    pts2: list[int] = []
    wav_r2 = int(mid_r * 0.83) + int(ae * 0.7)
    wave_amp2 = 7 + 14 * amp
    for ang in _orb_angles_96:
        wobble = (math.sin(t * 1.7 + ang * 4.0 + 1.2) + 0.55 * math.sin(t * 2.6 + ang * 9.0 - 0.7)) * 0.5
        rad = wav_r2 + wobble * wave_amp2
        pts2.extend([int(cx + rad * math.cos(ang)), int(cy + rad * math.sin(ang))])
    canvas.create_line(*pts2, fill=_shade(HUD_CYAN, 0.7), width=2, smooth=True, splinesteps=12, tags="dynamic")

    # small orbiting particles
    pr = int(mid_r * 0.90)
    for i, ang in enumerate(_orb_angles_60[::2]):
        a = ang + math.radians(a1 * 0.6) + (0.3 if i % 2 else 0)
        rr_p = pr + int(10 * math.sin(t * 2.5 + i))
        px = cx + rr_p * math.cos(a)
        py = cy + rr_p * math.sin(a)
        s = 2 + (i % 3)
        canvas.create_oval(px - s, py - s, px + s, py + s,
                           fill=HUD_CYAN if i % 3 else HUD_BLUE, outline="", tags="dynamic")

    # --- central sphere with mesh ---
    core_col = HUD_ACCENT if _command_active.is_set() else "#00E6FF"
    # inner glow gradient
    for i in range(7):
        tt = i / 6.0
        rr3 = int(_lerp(inner_r + 14, inner_r - 2, tt))
        col = _lerp_color("#003A45", core_col, (1 - tt) * 0.55 + amp * 0.25)
        canvas.create_oval(cx - rr3, cy - rr3, cx + rr3, cy + rr3, outline=col, width=3, tags="dynamic")
    canvas.create_oval(cx - inner_r - 10, cy - inner_r - 10, cx + inner_r + 10, cy + inner_r + 10, outline=HUD_DIM, width=2, tags="dynamic")
    canvas.create_oval(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, fill=core_col, outline="", tags="dynamic")

    # mesh (latitudes)
    for k in range(-3, 4):
        ry = int(inner_r * (0.22 + 0.11 * abs(k)))
        rx = int(inner_r * 0.95)
        y = cy + int(k * inner_r * 0.12)
        canvas.create_oval(cx - rx, y - ry, cx + rx, y + ry, outline="#9AFFFF" if amp > 0.25 else HUD_MID, width=1, tags="dynamic")

    # mesh (longitudes): arcs sweeping around
    for i in range(8):
        start = (a1 * 1.4 + i * 45) % 360
        canvas.create_arc(cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r, start=start, extent=140,
                          style="arc", outline="#B8FFFF" if i % 2 == 0 else HUD_MID, width=1, tags="dynamic")

    # hex-like micro grid in the core (tiny dots in rings)
    dot_r = int(inner_r * 0.78)
    for i in range(18):
        ang = math.radians((a1 * 2.2 + i * 20) % 360)
        rr_d = dot_r + int(6 * math.sin(t * 3.0 + i))
        px = cx + rr_d * math.cos(ang)
        py = cy + rr_d * math.sin(ang)
        s = 1 + (i % 2)
        canvas.create_oval(px - s, py - s, px + s, py + s, fill="white" if i % 6 == 0 else "#A8FFFF", outline="", tags="dynamic")

    # circuit spokes (thin lines with nodes)
    spoke_r1 = int(inner_r * 0.35)
    spoke_r2 = int(inner_r * 0.98)
    for i in range(12):
        ang = math.radians((a1 * 0.7 + i * 30) % 360)
        x1 = cx + spoke_r1 * math.cos(ang)
        y1 = cy + spoke_r1 * math.sin(ang)
        x2 = cx + spoke_r2 * math.cos(ang)
        y2 = cy + spoke_r2 * math.sin(ang)
        canvas.create_line(x1, y1, x2, y2, fill=HUD_DIM, width=1, tags="dynamic")
        nx = cx + (spoke_r1 + (spoke_r2 - spoke_r1) * 0.62) * math.cos(ang)
        ny = cy + (spoke_r1 + (spoke_r2 - spoke_r1) * 0.62) * math.sin(ang)
        canvas.create_oval(nx - 2, ny - 2, nx + 2, ny + 2, fill=HUD_CYAN, outline="", tags="dynamic")

    # center highlight
    dot = max(4, int(inner_r * 0.10))
    canvas.create_oval(cx - dot, cy - dot, cx + dot, cy + dot, fill="white", outline="", tags="dynamic")

    # activity pulse ring when VAD is active
    if _vad_active.is_set():
        gp = _pulse(8, 8, 18)
        canvas.create_oval(cx - gp, cy - gp, cx + gp, cy + gp, fill="", outline=HUD_ACCENT, width=3, tags="dynamic")


def _panel(x0: int, y0: int, w: int, h: int, title: str, tag: str = "static"):
    canvas.create_rectangle(
        x0, y0, x0 + w, y0 + h,
        fill=HUD_PANEL_BG, outline=HUD_MID, width=1, dash=(4, 5),
        tags=tag,
    )
    canvas.create_text(
        x0 + 10, y0 + 14, text=title,
        fill=HUD_CYAN, font=("Courier", 10, "bold"),
        anchor="w", tags=tag,
    )
    canvas.create_line(x0 + 8, y0 + 26, x0 + w - 8, y0 + 26, fill=HUD_DIM, tags=tag)


def _draw_top_bar():
    canvas.create_rectangle(0, 0, W, 88, fill=HUD_BG, outline="", tags="static")
    canvas.create_line(0, 88, W, 88, fill=HUD_MID, width=1, tags="static")

    # left status strip
    canvas.create_text(12, 14, text="ONLINE", fill=HUD_GREEN, font=("Courier", 9, "bold"), anchor="w", tags="static")
    canvas.create_text(12, 32, text="VOICE", fill=HUD_DIM, font=("Courier", 8), anchor="w", tags="static")
    canvas.create_text(12, 48, text="ASR", fill=HUD_DIM, font=("Courier", 8), anchor="w", tags="static")

    # center title
    canvas.create_text(cx, 28, text="J.A.R.V.I.S.", fill=HUD_CYAN, font=("Courier", 26, "bold"), anchor="center", tags="static")
    canvas.create_text(
        cx, 54,
        text="HUD INTERFACE  |  LOCAL PROCESSING  |  OFFLINE MODE",
        fill=HUD_MID, font=("Courier", 9), anchor="center", tags="static",
    )

    # right time
    canvas.create_text(W - 12, 16, text=datetime.datetime.now().strftime("%a, %b %d, %Y"), fill=HUD_DIM, font=("Courier", 8), anchor="e", tags="static")
    canvas.create_text(W - 12, 34, text=datetime.datetime.now().strftime("%H:%M:%S"), fill=HUD_CYAN, font=("Courier", 14, "bold"), anchor="e", tags="static")
    fs_hint = "[ESC] JANELA" if _fullscreen else "[F11] CINEMA"
    canvas.create_text(W - 12, 56, text=fs_hint, fill=HUD_MID, font=("Courier", 8), anchor="e", tags="static")


def _draw_center_frames_static():
    # bottom center mini-panels like the reference (empty frames; filled dynamically)
    y0 = int(H * 0.58)
    h = int(H * 0.22)
    margin = 18
    w = int((W * 0.54 - margin) / 2)
    x0 = int(W * 0.23)
    _panel(x0, y0, w, h, "SIGNAL MATRIX", tag="static")
    _panel(x0 + w + margin, y0, w, h, "I/O MONITOR", tag="static")


def _draw_left_column_static():
    x0 = 16
    col_w = max(260, int(W * 0.20))
    y = 100
    gap = 14

    _panel(x0, y, col_w, 160, "TASK QUEUE", tag="static")
    y += 160 + gap
    _panel(x0, y, col_w, 260, "SYSTEM STATUS", tag="static")
    y += 260 + gap
    _panel(x0, y, col_w, 210, "ACTIVE PROCESSES", tag="static")
    y += 210 + gap
    _panel(x0, y, col_w, max(120, H - y - 80), "POWER STATUS", tag="static")


def _draw_right_column_static():
    col_w = max(300, int(W * 0.22))
    x0 = W - col_w - 16
    y = 100
    gap = 14

    _panel(x0, y, col_w, 170, "ASSISTANT LOG", tag="static")
    y += 170 + gap
    _panel(x0, y, col_w, 210, "ATMOSPHERIC DATA", tag="static")
    y += 210 + gap
    _panel(x0, y, col_w, 160, "SECURITY STATUS", tag="static")
    y += 160 + gap
    _panel(x0, y, col_w, 170, "NOW PLAYING", tag="static")
    y += 170 + gap
    _panel(x0, y, col_w, max(120, H - y - 80), "SERVER NODES", tag="static")


def _draw_left_column_dynamic():
    x0 = 16
    col_w = max(260, int(W * 0.20))
    y = 100
    gap = 14

    # TASK QUEUE (use recent status lines)
    entries = _status_log[-6:]
    for i, line in enumerate(reversed(entries)):
        yy = y + 40 + i * 18
        txt = line[:38] + "..." if len(line) > 41 else line
        canvas.create_text(x0 + 12, yy, text=f"• {txt}", fill=HUD_MID if i else HUD_CYAN, font=("Courier", 8, "bold" if i == 0 else "normal"), anchor="w", tags="dynamic")
    if not entries:
        canvas.create_text(x0 + 12, y + 55, text="(vazio)", fill=HUD_DIM, font=("Courier", 9, "italic"), anchor="w", tags="dynamic")

    y += 160 + gap

    # SYSTEM STATUS
    m = _get_sys_metrics()
    net = _get_net_metrics()

    cpu = float(m.get("cpu", 0.0))
    ram = float(m.get("ram", 0.0))
    disk = float(m.get("disk", 0.0))
    temp = m.get("temp", None)
    uptime = m.get("uptime", "00:00:00")

    def _metric_color(pct: float) -> str:
        if pct >= 85:
            return HUD_ACCENT
        if pct >= 60:
            return HUD_YELLOW
        return HUD_CYAN

    rows = [
        ("UPTIME", uptime, HUD_GREEN, None),
        ("CPU", f"{cpu:.0f}%", _metric_color(cpu), cpu / 100.0),
        ("RAM", f"{ram:.0f}%", _metric_color(ram), ram / 100.0),
        ("DISK", f"{disk:.0f}%", _metric_color(disk), disk / 100.0),
        ("TEMP", f"{temp:.0f}C" if temp is not None else "N/A", HUD_GREEN if (temp or 0) < 65 else (HUD_YELLOW if (temp or 0) < 80 else HUD_ACCENT), min(((temp or 0) / 100.0), 1.0) if temp is not None else None),
        ("IP", net.get("ip", "N/A"), HUD_MID, None),
        ("VOICE", "CMD" if _command_active.is_set() else "LISTEN", HUD_ACCENT if _command_active.is_set() else HUD_GREEN, None),
        ("VAD", "SPEECH" if _vad_active.is_set() else "SILENCE", HUD_ACCENT if _vad_active.is_set() else HUD_DIM, None),
    ]
    bar_w = int(col_w * 0.62)
    for i, (k, v, col, pct) in enumerate(rows):
        yy = y + 44 + i * 26
        canvas.create_text(x0 + 12, yy, text=k, fill=HUD_DIM, font=("Courier", 8), anchor="w", tags="dynamic")
        canvas.create_text(x0 + 86, yy, text=v, fill=col, font=("Courier", 9, "bold"), anchor="w", tags="dynamic")
        if pct is not None:
            bx0 = x0 + 12
            by0 = yy + 10
            canvas.create_rectangle(bx0, by0, bx0 + bar_w, by0 + 6, fill="#001820", outline="", tags="dynamic")
            canvas.create_rectangle(bx0, by0, bx0 + int(bar_w * max(0.0, min(1.0, pct))), by0 + 6, fill=col, outline="", tags="dynamic")

    y += 260 + gap

    # ACTIVE PROCESSES
    procs = _get_top_processes()
    for i, p in enumerate(procs[:6]):
        yy = y + 44 + i * 22
        name = p["name"][:18] + "…" if len(p["name"]) > 19 else p["name"]
        cpu_p = p["cpu"]
        mem_p = p["mem"]
        col = HUD_ACCENT if cpu_p >= 70 else (HUD_YELLOW if cpu_p >= 30 else HUD_MID)
        canvas.create_text(x0 + 12, yy, text=f"{name: <19}", fill=HUD_CYAN, font=("Courier", 8, "bold"), anchor="w", tags="dynamic")
        canvas.create_text(x0 + col_w - 12, yy, text=f"{cpu_p:>4.0f}%  {mem_p:>4.0f}%", fill=col, font=("Courier", 8), anchor="e", tags="dynamic")
    if not procs:
        canvas.create_text(x0 + 12, y + 55, text="(indisponível)", fill=HUD_DIM, font=("Courier", 9, "italic"), anchor="w", tags="dynamic")

    y += 210 + gap

    # POWER STATUS
    batt = None
    try:
        batt = psutil.sensors_battery()
    except Exception:
        batt = None

    if batt is None:
        canvas.create_text(x0 + 12, y + 55, text="BATERIA: N/A", fill=HUD_DIM, font=("Courier", 9, "bold"), anchor="w", tags="dynamic")
        canvas.create_text(x0 + 12, y + 80, text="AC: N/A", fill=HUD_DIM, font=("Courier", 9), anchor="w", tags="dynamic")
    else:
        pct = float(batt.percent or 0.0)
        on_ac = bool(batt.power_plugged)
        col = HUD_GREEN if pct >= 60 else (HUD_YELLOW if pct >= 25 else HUD_ACCENT)
        canvas.create_text(x0 + 12, y + 50, text=f"BATERIA: {pct:.0f}%", fill=col, font=("Courier", 12, "bold"), anchor="w", tags="dynamic")
        canvas.create_text(x0 + 12, y + 74, text=f"AC LINE: {'ON' if on_ac else 'OFF'}", fill=HUD_GREEN if on_ac else HUD_DIM, font=("Courier", 9, "bold"), anchor="w", tags="dynamic")
        # bar
        bx0 = x0 + 12
        by0 = y + 96
        bw = int(col_w * 0.80)
        canvas.create_rectangle(bx0, by0, bx0 + bw, by0 + 10, fill="#001820", outline=HUD_DIM, tags="dynamic")
        canvas.create_rectangle(bx0, by0, bx0 + int(bw * pct / 100.0), by0 + 10, fill=col, outline="", tags="dynamic")


def _draw_right_column_dynamic():
    col_w = max(300, int(W * 0.22))
    x0 = W - col_w - 16
    y = 100
    gap = 14

    # ASSISTANT LOG (use command history + statuses)
    logs = []
    for cmd, ts in list(zip(_history_log, _history_ts))[-4:]:
        logs.append((f"[{ts}] > {cmd}", HUD_GREEN))
    for s in _status_log[-3:]:
        logs.append((s, HUD_MID))
    logs = logs[-7:]
    for i, (line, col) in enumerate(reversed(logs)):
        yy = y + 42 + i * 18
        txt = line[:42] + "..." if len(line) > 45 else line
        canvas.create_text(x0 + 12, yy, text=txt, fill=col if i else HUD_CYAN, font=("Courier", 8, "bold" if i == 0 else "normal"), anchor="w", tags="dynamic")
    if not logs:
        canvas.create_text(x0 + 12, y + 55, text="(aguardando eventos...)", fill=HUD_DIM, font=("Courier", 9, "italic"), anchor="w", tags="dynamic")

    y += 170 + gap

    # ATMOSPHERIC DATA (offline-friendly: use CPU temp if available)
    m = _get_sys_metrics()
    temp = m.get("temp", None)
    temp_str = f"{temp:.0f}C" if temp is not None else "N/A"
    canvas.create_text(x0 + 12, y + 52, text=f"TEMP (SENSOR): {temp_str}", fill=HUD_CYAN, font=("Courier", 12, "bold"), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 82, text="HUMIDITY: N/A", fill=HUD_DIM, font=("Courier", 9), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 104, text="PRESSURE: N/A", fill=HUD_DIM, font=("Courier", 9), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 130, text="SKY: OFFLINE", fill=HUD_MID, font=("Courier", 9, "bold"), anchor="w", tags="dynamic")

    y += 210 + gap

    # SECURITY STATUS (simple heuristic)
    cpu = float(m.get("cpu", 0.0))
    threat = "LOW"
    tcol = HUD_GREEN
    if cpu >= 90:
        threat = "ELEVATED"
        tcol = HUD_ACCENT
    canvas.create_text(x0 + 12, y + 54, text=f"THREAT LEVEL: {threat}", fill=tcol, font=("Courier", 12, "bold"), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 82, text="FIREWALL: (OS)", fill=HUD_DIM, font=("Courier", 9), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 104, text="INTRUSION: NONE", fill=HUD_MID, font=("Courier", 9, "bold"), anchor="w", tags="dynamic")

    y += 160 + gap

    # NOW PLAYING (placeholder but stable/offline)
    canvas.create_text(x0 + 12, y + 54, text="SOURCE: N/A", fill=HUD_DIM, font=("Courier", 9), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 82, text="TRACK: (no session)", fill=HUD_MID, font=("Courier", 10, "bold"), anchor="w", tags="dynamic")
    # small fake EQ reacting to mic amplitude
    base_y = y + 140
    bars = 18
    bw = int((col_w - 24) / bars)
    for i in range(bars):
        h = int(8 + 50 * abs(math.sin(time.time() * 2 + i * 0.5)) * (0.35 + 0.65 * _amp_smooth))
        bx = x0 + 12 + i * bw
        canvas.create_rectangle(bx, base_y - h, bx + bw - 3, base_y, fill=HUD_CYAN if i % 3 else HUD_ACCENT, outline="", tags="dynamic")

    y += 170 + gap

    # SERVER NODES (local network I/O)
    net = _get_net_metrics()
    canvas.create_text(x0 + 12, y + 54, text=f"LOCAL: {net.get('ip', 'N/A')}", fill=HUD_CYAN, font=("Courier", 10, "bold"), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 80, text=f"DOWN: {_fmt_rate(net.get('down_bps', 0.0))}", fill=HUD_MID, font=("Courier", 9), anchor="w", tags="dynamic")
    canvas.create_text(x0 + 12, y + 102, text=f"UP  : {_fmt_rate(net.get('up_bps', 0.0))}", fill=HUD_MID, font=("Courier", 9), anchor="w", tags="dynamic")


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
    net = _get_net_metrics()
    canvas.create_text(W-12, y0+24, text=f"IP {net.get('ip', 'N/A')}  |  NET ↓{_fmt_rate(net.get('down_bps', 0.0))} ↑{_fmt_rate(net.get('up_bps', 0.0))}",
                       fill=HUD_DIM, font=("Courier",8), anchor="e", tags="dynamic")
    # note: whisper_asr imported later in main to avoid dependency loop
    from jarvis.voice.transcriber import whisper_asr
    w_col = HUD_GREEN if whisper_asr.ready else HUD_YELLOW
    model_label = (WHISPER_MODEL or "local").upper()
    w_txt = f"WHISPER [{model_label}] READY" if whisper_asr.ready \
            else f"WHISPER [{model_label}] LOADING..."
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


