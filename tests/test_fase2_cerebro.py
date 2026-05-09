# tests/test_fase2_cerebro.py
#
# COPILOT: Implemente este arquivo de testes completo.
# Testes de LLM requerem Ollama rodando em localhost:11434.

import pytest
import time
from pathlib import Path


# ── TESTES DA MEMÓRIA ─────────────────────────────────────────────────────────

def test_memory_importa():
    from jarvis.brain.memory import Memory
    assert Memory is not None

def test_memory_instancia_e_cria_pasta():
    """Verifica se Memory cria a pasta jarvis/data/ automaticamente."""
    from jarvis.brain.memory import Memory
    m = Memory()
    assert Path("jarvis/data").exists(), "Pasta jarvis/data não foi criada"

def test_memory_adicionar_mensagens():
    """
    COPILOT: Verifica ciclo completo de adição de mensagens.
    - Limpar, adicionar user + assistant, verificar get_messages()
    - Roles devem ser: system, user, assistant (nesta ordem)
    """
    from jarvis.brain.memory import Memory
    m = Memory()
    m.clear()
    m.add_user("olá")
    m.add_assistant("olá senhor")
    msgs = m.get_messages()
    assert len(msgs) >= 3, f"Esperado >=3 mensagens, obteve {len(msgs)}"
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"
    assert msgs[2]["role"] == "assistant"

def test_memory_trim():
    """
    COPILOT: Verifica que o histórico é limitado ao MAX_HISTORY_TURNS.
    - Adicionar 50 pares de mensagens
    - get_messages() deve ter no máximo MAX_HISTORY_TURNS*2 + 1 (system)
    """
    from jarvis.brain.memory import Memory, MAX_HISTORY_TURNS
    m = Memory()
    m.clear()
    for i in range(50):
        m.add_user(f"mensagem {i}")
        m.add_assistant(f"resposta {i}")
    msgs = m.get_messages()
    max_esperado = MAX_HISTORY_TURNS * 2 + 1
    assert len(msgs) <= max_esperado, \
        f"Histórico não foi truncado: {len(msgs)} > {max_esperado}"

def test_memory_persistencia():
    """
    COPILOT: Verifica que o histórico é salvo e recarregado do disco.
    - Instância 1: adicionar mensagens, aguardar 1.5s para escrita
    - Instância 2: verificar que as mensagens foram carregadas
    """
    from jarvis.brain.memory import Memory
    m1 = Memory()
    m1.clear()
    m1.add_user("mensagem persistida")
    m1.add_assistant("resposta persistida")
    time.sleep(1.5)

    m2 = Memory()
    textos = [msg["content"] for msg in m2.get_messages()]
    assert "mensagem persistida" in textos, "Mensagem não foi persistida no disco"


# ── TESTES DO LLM ─────────────────────────────────────────────────────────────

def test_llm_importa():
    from jarvis.brain.llm import LLM
    assert LLM is not None

@pytest.mark.timeout(10)
def test_llm_verifica_ollama_sem_excecao():
    """Verifica que LLM instancia sem lançar exceção (mesmo se Ollama estiver offline)."""
    from jarvis.brain.llm import LLM
    llm = LLM()
    assert llm is not None

@pytest.mark.timeout(90)
def test_llm_responde_pergunta_simples():
    """
    COPILOT: Verifica que LLM retorna string não vazia.
    REQUER: Ollama rodando com llama3.
    """
    from jarvis.brain.llm import LLM
    llm = LLM()
    messages = [
        {"role": "system", "content": "Responda apenas 'ok' a qualquer mensagem."},
        {"role": "user", "content": "teste"}
    ]
    resposta = llm.ask(messages)
    assert isinstance(resposta, str) and len(resposta) > 0

@pytest.mark.timeout(10)
def test_llm_sem_ollama_retorna_mensagem_amigavel():
    """
    COPILOT: Verifica que LLM retorna mensagem amigável quando Ollama está offline.
    - Usar URL inválida (monkeypatch), chamar ask(), deve retornar string (não exceção)
    """
    from jarvis.brain import llm as llm_module
    original_url = llm_module.OLLAMA_URL
    llm_module.OLLAMA_URL = "http://localhost:99999/api/chat"

    from jarvis.brain.llm import LLM
    llm = LLM()
    resposta = llm.ask([{"role": "user", "content": "teste"}])
    llm_module.OLLAMA_URL = original_url

    assert isinstance(resposta, str) and len(resposta) > 0


# ── TESTES DO BRAIN ───────────────────────────────────────────────────────────

def test_brain_importa():
    from jarvis.brain.brain import Brain
    assert Brain is not None

@pytest.mark.timeout(90)
def test_brain_think_retorna_string():
    """REQUER: Ollama rodando. Verifica que think() retorna string não vazia."""
    from jarvis.brain.brain import Brain
    brain = Brain()
    resposta = brain.think("Responda apenas: ok")
    assert isinstance(resposta, str) and len(resposta) > 0

def test_brain_reset_memory():
    """
    COPILOT: Verifica que reset_memory() deixa apenas o system prompt no histórico.
    """
    from jarvis.brain.brain import Brain
    brain = Brain()
    brain.memory.add_user("teste")
    brain.memory.add_assistant("ok")
    brain.reset_memory()
    msgs = brain.memory.get_messages()
    assert len(msgs) == 2 and msgs[0]["role"] == "system" and msgs[1]["role"] == "system"