# jarvis/vision/vision_llm.py
#
# Módulo de visão com LLaVA (Ollama multimodal)
# Interpreta imagens e responde perguntas sobre conteúdo visual

import requests
import base64
import time
from io import BytesIO
from PIL import Image
from jarvis import core

LLAVA_URL = "http://localhost:11434/api/generate"
LLAVA_MODEL = "llava"

class VisionLLM:
    """
    Visão via LLaVA — modelo multimodal que entende imagens + texto.
    """

    def __init__(self):
        self._check_llava()

    def _check_llava(self):
        """
        Verifica se LLaVA está disponível.
        """
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=3)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                if any("llava" in name for name in model_names):
                    core.log.info("LLaVA disponível ✓")
                    return
            
            core.log.info("AVISO: LLaVA não encontrado. Execute: ollama pull llava")
        except Exception as e:
            core.log.info(f"AVISO: Ollama pode não estar respondendo: {e}")

    def describe_screen(self, image: Image.Image) -> str:
        """
        Descreve o que está visível na tela.
        """
        base64_str = self._image_to_base64(image)
        prompt = """Descreva detalhadamente o que você vê nesta captura de tela.
Mencione: aplicativos abertos, texto visível, janelas, botões,
mensagens de erro se houver. Responda em português."""
        
        return self._ask_llava(prompt, base64_str)

    def answer_about_screen(self, image: Image.Image, question: str) -> str:
        """
        Responde uma pergunta sobre o conteúdo da tela.
        """
        base64_str = self._image_to_base64(image)
        prompt = f"Analise esta captura de tela e responda em português: {question}"
        
        return self._ask_llava(prompt, base64_str)

    def read_error_message(self, image: Image.Image) -> str:
        """
        Detecta e descreve mensagens de erro na tela.
        """
        base64_str = self._image_to_base64(image)
        prompt = """Existe alguma mensagem de erro nesta tela? Se sim, transcreva-a
exatamente e explique o que significa em português. Se não há erro,
diga 'Nenhum erro detectado.'"""
        
        return self._ask_llava(prompt, base64_str)

    def find_element(self, image: Image.Image, element_description: str) -> str:
        """
        Localiza um elemento visual descrito em linguagem natural.
        """
        base64_str = self._image_to_base64(image)
        prompt = f"""Nesta imagem, localize: '{element_description}'.
Descreva sua posição (ex: 'canto superior direito', 'centro da tela')
e se está visível ou não. Responda em português."""
        
        return self._ask_llava(prompt, base64_str)

    def _ask_llava(self, prompt: str, base64_image: str) -> str:
        """
        Envia a pergunta para LLaVA via Ollama.
        """
        try:
            payload = {
                "model": LLAVA_MODEL,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False
            }
            
            start_time = time.time()
            response = requests.post(
                LLAVA_URL,
                json=payload,
                timeout=(5, 120)
            )
            response.raise_for_status()
            
            result = response.json()
            text = result.get("response", "")
            elapsed = time.time() - start_time
            
            core.log.info(f"LLaVA respondeu em {elapsed:.1f}s")
            return text.strip()
            
        except requests.exceptions.ConnectionError:
            core.log.info("LLaVA não está disponível. Certifique-se que Ollama está rodando.")
            return "Desculpe, o módulo de visão não está disponível."
        except requests.exceptions.Timeout:
            core.log.info("Timeout ao aguardar resposta do LLaVA")
            return "Desculpe, a análise de imagem demorou muito."
        except KeyError:
            core.log.info("Formato inesperado na resposta do LLaVA")
            return "Erro ao processar resposta de visão."
        except Exception as e:
            core.log.info(f"Erro em LLaVA: {e}")
            return f"Erro na análise de imagem: {e}"

    def _image_to_base64(self, image: Image.Image) -> str:
        """
        Converte PIL Image para string base64.
        """
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')