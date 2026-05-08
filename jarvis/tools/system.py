import subprocess
import os
import time
import pyautogui
import psutil
import ctypes
from pathlib import Path
from jarvis import core

# Segurança do pyautogui
pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = True

# Mapeamento de nomes de apps
APP_MAPPING = {
    "bloco de notas": "notepad",
    "notepad": "notepad",
    "calculadora": "calc",
    "calculator": "calc",
    "chrome": "chrome",
    "google chrome": "chrome",
    "firefox": "firefox",
    "explorador": "explorer",
    "explorer": "explorer",
    "arquivos": "explorer",
    "word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "microsoft excel": "excel",
    "paint": "mspaint",
    "cmd": "cmd",
    "terminal": "cmd",
    "prompt": "cmd",
    "spotify": "spotify"
}

def open_app(name: str) -> str:
    core.log.info(f"Abrindo aplicativo: {name}")
    try:
        # Mapear nome
        mapped_name = APP_MAPPING.get(name.lower(), name)
        
        # Tentar abrir
        if os.name == 'nt':  # Windows
            try:
                os.startfile(mapped_name)
                return f"Aplicativo '{name}' aberto com sucesso."
            except FileNotFoundError:
                try:
                    subprocess.Popen([mapped_name])
                    return f"Aplicativo '{name}' aberto com sucesso."
                except FileNotFoundError:
                    subprocess.Popen(["start", mapped_name], shell=True)
                    return f"Aplicativo '{name}' aberto com sucesso."
        else:
            subprocess.Popen([mapped_name])
            return f"Aplicativo '{name}' aberto com sucesso."
    except Exception as e:
        core.log.info(f"Erro ao abrir {name}: {e}")
        return f"Erro ao abrir aplicativo '{name}': {str(e)}"

def close_app(name: str) -> str:
    core.log.info(f"Fechando aplicativo: {name}")
    try:
        closed = []
        for proc in psutil.process_iter(['name']):
            try:
                if name.lower() in proc.info['name'].lower():
                    proc.terminate()
                    closed.append(proc.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        if closed:
            time.sleep(1)  # Aguardar encerramento
            return f"Aplicativo(s) fechado(s): {', '.join(closed)}"
        else:
            return f"Nenhum processo '{name}' encontrado."
    except Exception as e:
        core.log.info(f"Erro ao fechar {name}: {e}")
        return f"Erro ao fechar aplicativo '{name}': {str(e)}"

def take_screenshot(filename: str = None) -> str:
    core.log.info("Capturando screenshot")
    try:
        if filename is None:
            filename = f"screenshot_{int(time.time())}.png"
        
        # Criar pasta se não existir
        screenshot_dir = Path("jarvis/data/screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)
        
        path = screenshot_dir / filename
        pyautogui.screenshot(str(path))
        return f"Screenshot salva em {path}"
    except Exception as e:
        core.log(f"Erro no screenshot: {e}")
        return f"Erro ao capturar screenshot: {str(e)}"

def get_running_apps() -> str:
    core.log("Listando aplicativos em execução")
    try:
        apps = []
        for proc in psutil.process_iter(['name', 'cpu_percent']):
            try:
                if proc.info['cpu_percent'] > 0:
                    apps.append((proc.info['name'], proc.info['cpu_percent']))
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Ordenar por CPU e pegar top 10
        apps.sort(key=lambda x: x[1], reverse=True)
        apps = apps[:10]
        
        if apps:
            result = "Aplicativos em execução:\n"
            for name, cpu in apps:
                result += f"- {name} ({cpu:.1f}% CPU)\n"
            return result.strip()
        else:
            return "Nenhum aplicativo em execução detectado."
    except Exception as e:
        core.log(f"Erro ao listar apps: {e}")
        return f"Erro ao listar aplicativos: {str(e)}"

def type_text(text: str) -> str:
    core.log(f"Digitando texto: {text[:50]}...")
    try:
        time.sleep(0.5)  # Aguardar foco na janela
        
        # Usar clipboard para texto com acentos
        import pyperclip
        pyperclip.copy(text)
        pyautogui.hotkey('ctrl', 'v')
        
        return "Texto digitado com sucesso."
    except Exception as e:
        core.log(f"Erro ao digitar texto: {e}")
        return f"Erro ao digitar texto: {str(e)}"

def press_key(key: str) -> str:
    core.log(f"Pressionando tecla: {key}")
    try:
        if '+' in key:
            # Combinação
            keys = key.split('+')
            pyautogui.hotkey(*keys)
        else:
            # Tecla simples
            pyautogui.press(key)
        return f"Tecla '{key}' pressionada."
    except Exception as e:
        core.log(f"Erro ao pressionar {key}: {e}")
        return f"Erro ao pressionar tecla '{key}': {str(e)}"

def set_volume(level: int) -> str:
    core.log(f"Ajustando volume para {level}%")
    try:
        # Usar nircmd se disponível, senão tentar outro método
        try:
            volume_value = int(level * 655.35)  # 0-65535 range
            subprocess.run(['nircmd', 'setsysvolume', str(volume_value)], 
                         capture_output=True, check=True)
            return f"Volume ajustado para {level}%"
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback: usar PowerShell
            script = f'(New-Object -ComObject WScript.Shell).SendKeys([char]173); Start-Sleep -Milliseconds 100; ' * (10 - level // 10)
            subprocess.run(['powershell', '-Command', script], capture_output=True)
            return f"Volume aproximado ajustado para {level}% (usando método alternativo)"
    except Exception as e:
        core.log(f"Erro ao ajustar volume: {e}")
        return f"Erro ao ajustar volume: {str(e)}"

def lock_pc() -> str:
    core.log("Bloqueando estação de trabalho")
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Estação de trabalho bloqueada."
    except Exception as e:
        core.log(f"Erro ao bloquear PC: {e}")
        return f"Erro ao bloquear PC: {str(e)}"

def shutdown_pc(delay_seconds: int = 30) -> str:
    core.log(f"Agendando desligamento em {delay_seconds} segundos")
    try:
        subprocess.run(['shutdown', '/s', '/t', str(delay_seconds)], 
                     capture_output=True, check=True)
        return f"PC será desligado em {delay_seconds} segundos."
    except Exception as e:
        core.log(f"Erro ao agendar shutdown: {e}")
        return f"Erro ao agendar desligamento: {str(e)}"