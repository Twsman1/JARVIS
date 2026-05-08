import threading
import time
from jarvis import core

IDLE      = "idle"
LISTENING = "listening"
THINKING  = "thinking"
SPEAKING  = "speaking"
ACTING    = "acting"
ERROR     = "error"

_current_state  = IDLE
_current_action = ""
_last_user_text    = ""
_last_jarvis_text  = ""
_conversation_log  = []
_observers = []
_lock = threading.Lock()

def register_observer(callback):
    """Adicionar callback à lista _observers"""
    with _lock:
        _observers.append(callback)

def set_state(state: str, action: str = ""):
    """Atualizar estado e notificar observers"""
    global _current_state, _current_action
    with _lock:
        old_state = _current_state
        _current_state = state
        _current_action = action
    
    if old_state != state or action:
        core.log.info(f"Estado mudou: {old_state} → {state} ({action})")
        # Notificar observers em thread separada
        threading.Thread(target=_notify_observers, args=(state, action), daemon=True).start()

def _notify_observers(state, action):
    """Notificar todos os observers"""
    for callback in _observers:
        try:
            callback(state, action)
        except Exception as e:
            core.log.info(f"Erro ao notificar observer: {e}")

def add_to_log(role: str, text: str):
    """Adicionar entrada ao log de conversa"""
    global _last_user_text, _last_jarvis_text
    entry = {
        "role": role,
        "text": text,
        "time": time.strftime("%H:%M")
    }
    
    with _lock:
        _conversation_log.append(entry)
        # Manter apenas os últimos 10
        if len(_conversation_log) > 10:
            _conversation_log.pop(0)
        
        if role == "user":
            _last_user_text = text
        elif role == "jarvis":
            _last_jarvis_text = text
    
    # Notificar observers
    _notify_observers(_current_state, _current_action)

def get_state() -> tuple[str, str]:
    """Retornar estado atual"""
    with _lock:
        return (_current_state, _current_action)

def get_conversation_log() -> list:
    """Retornar cópia do log de conversa"""
    with _lock:
        return _conversation_log.copy()