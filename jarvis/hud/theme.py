"""
HUD theme constants.

This module centralizes the color palette and sizing used by the Tkinter HUD.
Some legacy widgets import names like AZUL_PRIMARIO / BRANCO_TEXTO; those are
kept as aliases to avoid runtime errors.
"""

# Primary palette (inspired by the reference "Jarvis HUD" look)
HUD_CYAN    = "#00F5FF"
HUD_BLUE    = "#1AA3FF"
HUD_ACCENT  = "#FF7A18"
HUD_GREEN   = "#00FF88"
HUD_YELLOW  = "#FFCC00"
HUD_RED     = "#FF4444"

HUD_DIM     = "#003A45"
HUD_MID     = "#004D5C"
HUD_BG      = "#000D10"
HUD_GRID    = "#001A20"

# Panel fills
HUD_PANEL_BG = "#000A0E"
HUD_PANEL_BG_2 = "#00070A"

# Default window size
DEFAULT_W = 1280
DEFAULT_H = 800

# ---------------------------------------------------------------------------
# Compatibility aliases (used by older widgets)
# ---------------------------------------------------------------------------

AZUL_PRIMARIO = HUD_CYAN
AZUL_ESCURO   = HUD_PANEL_BG
VERDE_OK      = HUD_GREEN
AMARELO_AVISO = HUD_YELLOW
VERMELHO_ERRO = HUD_RED
BRANCO_TEXTO  = "#E0F0FF"
CINZA_TEXTO   = "#557799"
FUNDO         = HUD_BG

# Tkinter has no real alpha fill on canvas; use a darker fill as "translucent"
FUNDO_TRANSPARENTE = HUD_PANEL_BG_2
