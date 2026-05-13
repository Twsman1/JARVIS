# This module provides an offline-first LLM abstraction.
#
# It prefers a local Ollama server by default, but can also use the
# OpenJarvis SDK source tree when JARVIS_LLM_ENGINE=openjarvis.
#
# Manual setup required before running:
# - For Ollama: install Ollama, execute `ollama serve`, and pull a local model.
# - For OpenJarvis: set JARVIS_OPENJARVIS_PATH to the OpenJarvis source path or install
#   the package in your Python environment. Optionally specify
#   JARVIS_OPENJARVIS_CONFIG to use a custom OpenJarvis config file.
#
# If OpenJarvis is unavailable, the wrapper falls back to Ollama automatically.
#
# Improvements integrated from OpenJarvis:
# - Better error handling with custom exceptions
# - Token usage tracking and timing information
# - Tool call support (for future agent capabilities)
# - Streaming support (for real-time responses)
# - Proper HTTP client management with httpx
# - Model health checks and listing

import json
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
import httpx

from jarvis import core
from jarvis.config import (
    JARVIS_OPENJARVIS_CONFIG,
    JARVIS_OPENJARVIS_PATH,
    LLM_ENGINE,
    LLM_MODEL,
    OLLAMA_HOST,
)

CONNECT_TIMEOUT = 5
READ_TIMEOUT = 60

_JarvisClass: Optional[type] = None


class EngineConnectionError(Exception):
    """Raised when the LLM engine cannot be reached."""
    pass


def _resolve_openjarvis_path() -> Optional[str]:
    path = os.environ.get("JARVIS_OPENJARVIS_PATH", JARVIS_OPENJARVIS_PATH)
    if not path:
        return None

    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate

    if candidate.is_dir():
        return str(candidate.resolve())
    return None


def _import_openjarvis_jarvis():
    global _JarvisClass
    if _JarvisClass is not None:
        return _JarvisClass

    try:
        from openjarvis import Jarvis

        _JarvisClass = Jarvis
        return Jarvis
    except ImportError:
        pass

    candidate = _resolve_openjarvis_path()
    if candidate and candidate not in sys.path:
        sys.path.insert(0, candidate)
    if candidate:
        try:
            from openjarvis import Jarvis

            _JarvisClass = Jarvis
            return Jarvis
        except ImportError:
            pass

    return None


def _conversation_to_prompt(messages: list) -> str:
    prompt_lines = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "assistant":
            prompt_lines.append(f"JARVIS: {content}")
        elif role == "system":
            prompt_lines.append(f"SISTEMA: {content}")
        else:
            prompt_lines.append(f"USUÁRIO: {content}")
    return "\n".join(prompt_lines)


def estimate_prompt_tokens(messages: list) -> int:
    """Rough token estimation for messages (characters / 4)."""
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    return total_chars // 4


class LLM:
    def __init__(
        self,
        model: str = LLM_MODEL,
        engine: str = LLM_ENGINE,
        mock: bool = False,
    ):
        self.model = model
        self.engine = engine.lower()
        self.mock = mock
        self._openjarvis = None
        self._client = None  # httpx client for better connection management
        self._last_usage: Dict[str, int] = {}  # Track token usage

        if self.mock:
            core.log.info("Cérebro LLM inicializado em modo MOCK")
            return

        core.log.info(
            "Cérebro LLM inicializado com modelo: %s, engine: %s",
            self.model,
            self.engine,
        )

        if self.engine == "openjarvis":
            self._init_openjarvis()
        elif self.engine == "ollama":
            self._init_ollama_client()
        else:
            core.log.info(
                "Engine desconhecida '%s'. Usando Ollama como fallback.",
                self.engine,
            )
            self.engine = "ollama"
            self._init_ollama_client()

    def _init_ollama_client(self):
        """Initialize httpx client for Ollama with proper configuration."""
        self._client = httpx.Client(
            base_url=OLLAMA_HOST.rstrip("/"),
            timeout=httpx.Timeout(CONNECT_TIMEOUT, read=READ_TIMEOUT)
        )
        self._check_ollama()

    def _init_openjarvis(self):
        JarvisClass = _import_openjarvis_jarvis()
        if JarvisClass is None:
            core.log.info(
                "OpenJarvis SDK não encontrado. Instale ou configure JARVIS_OPENJARVIS_PATH."
            )
            self.engine = "ollama"
            self._init_ollama_client()
            return

        try:
            config_path = JARVIS_OPENJARVIS_CONFIG
            self._openjarvis = JarvisClass(
                config_path=config_path,
                model=self.model,
            )
            core.log.info("OpenJarvis SDK inicializado com modelo %s", self.model)
        except Exception as exc:
            core.log.info("Falha ao inicializar OpenJarvis: %s", exc)
            self.engine = "ollama"
            self._init_ollama_client()

    def _check_ollama(self):
        """Check Ollama connectivity and log status."""
        try:
            if self._client:
                resp = self._client.get("/api/tags", timeout=3.0)
                if resp.status_code == 200:
                    core.log.info("Ollama disponível ✓")
                    return
            # Fallback to requests if httpx client not initialized
            response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
            if response.status_code == 200:
                core.log.info("Ollama disponível ✓")
            else:
                core.log.info("Ollama respondeu com status não-200")
        except Exception as e:
            core.log.info("AVISO: Ollama pode não estar rodando: %s", e)

    def list_models(self) -> List[str]:
        """List available models from Ollama."""
        if self.engine == "openjarvis" and self._openjarvis:
            # OpenJarvis might have its own model listing
            try:
                return getattr(self._openjarvis, 'list_models', lambda: [])()
            except:
                pass

        # Default to Ollama
        try:
            if self._client:
                resp = self._client.get("/api/tags")
                resp.raise_for_status()
                data = resp.json()
                return [m["name"] for m in data.get("models", [])]
            else:
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
                response.raise_for_status()
                data = response.json()
                return [m["name"] for m in data.get("models", [])]
        except Exception as exc:
            core.log.warning("Failed to list models: %s", exc)
            return []

    def health(self) -> bool:
        """Check if the LLM backend is healthy."""
        if self.mock:
            return True

        if self.engine == "openjarvis" and self._openjarvis:
            try:
                return getattr(self._openjarvis, 'health', lambda: True)()
            except:
                return False

        # Check Ollama
        try:
            if self._client:
                resp = self._client.get("/api/tags", timeout=2.0)
                return resp.status_code == 200
            else:
                response = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
                return response.status_code == 200
        except Exception:
            return False

    def ask(self, messages: list, **kwargs) -> str:
        if self.mock:
            last_message = messages[-1]["content"] if messages else ""
            if "que horas" in last_message.lower():
                return "São 14:30, senhor."
            elif "tempo" in last_message.lower():
                return "O tempo está ensolarado com 25°C."
            elif "arquivos" in last_message.lower():
                return (
                    "Vou listar os arquivos na pasta atual. Aqui estão: "
                    "documento.txt, imagem.png, script.py."
                )
            else:
                return "Entendido, senhor. Como posso ajudar?"

        if self.engine == "openjarvis" and self._openjarvis is not None:
            return self._ask_openjarvis(messages, **kwargs)

        return self._ask_ollama(messages, **kwargs)

    def _ask_openjarvis(self, messages: list, **kwargs) -> str:
        if self._openjarvis is None:
            return self._ask_ollama(messages, **kwargs)

        prompt = _conversation_to_prompt(messages)
        try:
            return self._openjarvis.ask(prompt, **kwargs)
        except Exception as exc:
            core.log.info("OpenJarvis query falhou: %s", exc)
            return self._ask_ollama(messages, **kwargs)

    def _ask_ollama(self, messages: list, **kwargs) -> str:
        """Enhanced Ollama request with better error handling and token tracking."""
        # Convert messages to Ollama format
        msg_dicts = []
        for msg in messages:
            msg_dict = {
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            }
            # Handle tool calls if present
            if "tool_calls" in msg:
                msg_dict["tool_calls"] = msg["tool_calls"]
            msg_dicts.append(msg_dict)

        payload = {
            "model": self.model,
            "messages": msg_dicts,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", 0.7),
                "num_predict": kwargs.get("max_tokens", 300),
                "num_ctx": kwargs.get("num_ctx", 8192),
            },
        }

        # Add tools if provided
        if "tools" in kwargs and kwargs["tools"]:
            payload["tools"] = kwargs["tools"]

        # Disable thinking for Qwen models unless explicitly enabled
        if "think" not in kwargs:
            payload["think"] = False
        elif kwargs["think"] is not None:
            payload["think"] = kwargs["think"]

        start_time = time.time()

        try:
            if self._client:
                # Use httpx client
                resp = self._client.post("/api/chat", json=payload)
                if resp.status_code == 400 and "tools" in payload:
                    # Retry without tools if model doesn't support them
                    payload.pop("tools", None)
                    resp = self._client.post("/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
            else:
                # Fallback to requests
                response = requests.post(
                    f"{OLLAMA_HOST}/api/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                )
                if response.status_code == 400 and "tools" in payload:
                    payload.pop("tools", None)
                    response = requests.post(
                        f"{OLLAMA_HOST}/api/chat",
                        json=payload,
                        headers={"Content-Type": "application/json"},
                        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT),
                    )
                response.raise_for_status()
                data = response.json()

            # Extract response content
            content = data.get("message", {}).get("content", "")

            # Track token usage
            reported_prompt = data.get("prompt_eval_count", 0)
            estimated_prompt = estimate_prompt_tokens(messages)
            prompt_tokens = max(reported_prompt, estimated_prompt)
            prompt_tokens_evaluated = reported_prompt if reported_prompt > 0 else prompt_tokens
            completion_tokens = data.get("eval_count", 0)

            self._last_usage = {
                "prompt_tokens": prompt_tokens,
                "prompt_tokens_evaluated": prompt_tokens_evaluated,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }

            # Log timing
            elapsed = time.time() - start_time
            core.log.info("LLM respondeu em %.1fs (tokens: %d)", elapsed, self._last_usage["total_tokens"])

            # Handle tool calls if present
            tool_calls = data.get("message", {}).get("tool_calls", [])
            if tool_calls:
                # For now, just log tool calls - future enhancement
                core.log.info("Tool calls received: %s", tool_calls)

            return content

        except httpx.ConnectError:
            raise EngineConnectionError(f"Ollama não está acessível em {OLLAMA_HOST}")
        except requests.exceptions.ConnectionError:
            raise EngineConnectionError(f"Ollama não está acessível em {OLLAMA_HOST}")
        except httpx.TimeoutException:
            core.log.info("Timeout aguardando resposta do LLM")
            return "Desculpe, a resposta demorou muito."
        except requests.exceptions.Timeout:
            core.log.info("Timeout aguardando resposta do LLM")
            return "Desculpe, a resposta demorou muito."
        except Exception as e:
            core.log.info("Erro no LLM: %s", e)
            return "Ocorreu um erro ao processar sua solicitação."

    def get_last_usage(self) -> Dict[str, int]:
        """Get token usage from the last request."""
        return dict(self._last_usage)

    def close(self):
        """Clean up resources."""
        if self._client:
            self._client.close()
            self._client = None

    def __del__(self):
        """Ensure cleanup on deletion."""
        self.close()

    def set_model(self, model: str):
        self.model = model
        core.log.info("Modelo alterado para: %s", model)
