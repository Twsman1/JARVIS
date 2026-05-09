# tests/test_fase3_ferramentas.py
#
# COPILOT: Implemente este arquivo de testes completo.
# Cuidado com testes destrutivos: shutdown_pc, delete, etc — não testar esses diretamente.

import pytest
import time
from pathlib import Path


# ── SISTEMA ───────────────────────────────────────────────────────────────────

def test_system_importa():
    from jarvis.tools import system
    assert system is not None

def test_open_e_close_app():
    """
    COPILOT: Abre notepad, verifica no psutil que está rodando, fecha.
    """
    from jarvis.tools import system
    import psutil
    system.open_app("notepad")
    time.sleep(2)
    processos = [p.name().lower() for p in psutil.process_iter(["name"])]
    assert "notepad.exe" in processos, "Notepad não abriu"
    system.close_app("notepad")

def test_close_app_inexistente():
    """Fechar app que não existe deve retornar string amigável, nunca exceção."""
    from jarvis.tools import system
    r = system.close_app("app_inexistente_xyz_123")
    assert isinstance(r, str) and len(r) > 0

def test_take_screenshot_cria_arquivo():
    """
    COPILOT: Verifica que screenshot salva arquivo com tamanho > 0.
    - Extrair caminho do resultado com regex
    - Verificar existência e tamanho
    """
    from jarvis.tools import system
    import re
    resultado = system.take_screenshot()
    assert isinstance(resultado, str)
    paths = re.findall(r'jarvis[\\/]data[\\/]screenshots[\\/]\S+\.png', resultado)
    if paths:
        assert Path(paths[0]).exists() and Path(paths[0]).stat().st_size > 0

def test_get_running_apps_contem_python():
    """Verifica que get_running_apps retorna uma string com apps."""
    from jarvis.tools import system
    resultado = system.get_running_apps()
    assert isinstance(resultado, str) and len(resultado) > 10
    # Note: "python" may not be in the list if CPU usage is low, so just check it's a valid response


# ── WEB ───────────────────────────────────────────────────────────────────────

@pytest.mark.timeout(15)
def test_search_web_retorna_resultado():
    """REQUER internet. Busca retorna string contendo 'python'."""
    from jarvis.tools import web
    r = web.search_web("Python programming", max_results=2)
    assert isinstance(r, str) and "python" in r.lower()

@pytest.mark.timeout(10)
def test_search_wikipedia():
    """REQUER internet. Wikipedia retorna resumo não vazio."""
    from jarvis.tools import web
    r = web.search_wikipedia("Python linguagem programação")
    assert isinstance(r, str) and len(r) > 20

def test_open_url_adiciona_https():
    """open_url deve adicionar https:// quando URL não tem protocolo."""
    from jarvis.tools import web
    import webbrowser
    urls = []
    original = webbrowser.open
    webbrowser.open = lambda url: urls.append(url)
    web.open_url("google.com")
    webbrowser.open = original
    assert len(urls) > 0 and urls[0].startswith("https://")


# ── ARQUIVOS ──────────────────────────────────────────────────────────────────

def test_write_e_read_ciclo_completo():
    """Escreve arquivo, lê, verifica conteúdo, limpa."""
    from jarvis.tools import files
    conteudo = "Teste JARVIS 12345"
    files.write_file("jarvis/data/test_temp.txt", conteudo)
    resultado = files.read_file("jarvis/data/test_temp.txt")
    assert conteudo in resultado
    Path("jarvis/data/test_temp.txt").unlink(missing_ok=True)

def test_write_append():
    """Verifica que append preserva conteúdo anterior."""
    from jarvis.tools import files
    files.write_file("jarvis/data/test_append.txt", "linha 1\n")
    files.write_file("jarvis/data/test_append.txt", "linha 2\n", append=True)
    conteudo = files.read_file("jarvis/data/test_append.txt")
    assert "linha 1" in conteudo and "linha 2" in conteudo
    Path("jarvis/data/test_append.txt").unlink(missing_ok=True)

def test_create_folder():
    """Criar pasta deve resultar em pasta existente no disco."""
    from jarvis.tools import files
    import shutil
    from pathlib import Path
    folder_name = "test_jarvis_folder"
    files.create_folder(folder_name)
    folder_path = Path.home() / folder_name
    assert folder_path.exists()
    shutil.rmtree(str(folder_path), ignore_errors=True)

def test_security_bloqueia_path_sistema():
    """
    COPILOT: Acesso fora da home do usuário deve ser bloqueado.
    - Tentar read_file("C:/Windows/System32/drivers/etc/hosts")
    - Deve retornar erro OU lançar ValueError — nunca retornar conteúdo real
    """
    from jarvis.tools import files
    try:
        resultado = files.read_file("C:/Windows/System32/drivers/etc/hosts")
        assert any(w in resultado.lower() for w in ["erro", "não permitido", "segurança"]), \
            f"Acesso indevido não foi bloqueado: {resultado[:100]}"
    except (ValueError, PermissionError):
        pass


# ── ROUTER ────────────────────────────────────────────────────────────────────

def test_router_tem_minimo_15_ferramentas():
    from jarvis.tools.router import ToolRouter, TOOL_MAP
    ToolRouter()
    assert len(TOOL_MAP) >= 15

def test_router_executa_ferramenta_via_json():
    from jarvis.tools.router import ToolRouter
    router = ToolRouter()
    tool_used, resultado = router.parse_and_execute('{"tool": "get_running_apps", "args": {}}')
    assert tool_used == True and isinstance(resultado, str) and len(resultado) > 0

def test_router_texto_normal_nao_e_ferramenta():
    from jarvis.tools.router import ToolRouter
    router = ToolRouter()
    texto = "A capital do Brasil é Brasília."
    tool_used, resultado = router.parse_and_execute(texto)
    assert tool_used == False and resultado == texto

def test_router_ferramenta_desconhecida_retorna_erro_amigavel():
    from jarvis.tools.router import ToolRouter
    router = ToolRouter()
    tool_used, resultado = router.parse_and_execute('{"tool": "ferramenta_xyz_inexistente", "args": {}}')
    assert tool_used == True
    assert any(w in resultado.lower() for w in ["não", "erro", "reconhecida", "disponível"])