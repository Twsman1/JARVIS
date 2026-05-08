import requests
import json
import time
from jarvis import core

OLLAMA_URL = "http://localhost:11434/api/chat"
DEFAULT_MODEL = "llama3"
CONNECT_TIMEOUT = 5
READ_TIMEOUT = 60

class LLM:
    def __init__(self, model: str = DEFAULT_MODEL, mock: bool = False):
        self.model = model
        self.mock = mock
        if mock:
            core.log.info(f"Cérebro LLM inicializado em modo MOCK")
        else:
            core.log.info(f"Cérebro LLM inicializado com modelo: {model}")
            self._check_ollama()

    def _check_ollama(self):
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                core.log.info("Ollama disponível ✓")
            else:
                core.log.info("Ollama respondeu com status não-200")
        except Exception as e:
            core.log.info(f"AVISO: Ollama pode não estar rodando: {e}")

    def ask(self, messages: list) -> str:
        if self.mock:
            # Mock responses for testing
            last_message = messages[-1]["content"] if messages else ""
            if "que horas" in last_message.lower():
                return "São 14:30, senhor."
            elif "tempo" in last_message.lower():
                return "O tempo está ensolarado com 25°C."
            elif "arquivos" in last_message.lower():
                return "Vou listar os arquivos na pasta atual. Aqui estão: documento.txt, imagem.png, script.py."
            else:
                return "Entendido, senhor. Como posso ajudar?"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 300,
            }
        }
        start_time = time.time()
        try:
            response = requests.post(
                OLLAMA_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT)
            )
            response.raise_for_status()
            result = response.json()
            content = result["message"]["content"]
            elapsed = time.time() - start_time
            core.log.info(f"LLM respondeu em {elapsed:.1f}s")
            return content
        except requests.exceptions.ConnectionError:
            core.log.info("Ollama não está rodando. Inicie com: ollama serve")
            return "Desculpe, o sistema de IA local não está disponível."
        except requests.exceptions.Timeout:
            core.log.info("Timeout ao aguardar resposta do LLM")
            return "Desculpe, a resposta demorou muito."
        except Exception as e:
            core.log.info(f"Erro no LLM: {e}")
            return "Ocorreu um erro ao processar sua solicitação."

    def set_model(self, model: str):
        self.model = model
        core.log.info(f"Modelo alterado para: {model}")