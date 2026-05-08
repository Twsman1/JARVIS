# jarvis/tools/vision_tools.py
#
# Ferramentas de visão que o Agent pode usar
# Integram ScreenCapture + OCR + VisionLLM

from jarvis.vision.capture import ScreenCapture
from jarvis.vision.ocr import OCR
from jarvis.vision.vision_llm import VisionLLM
from jarvis import core
import pyautogui
import time

# Instâncias singleton
_capture = None
_ocr = None
_vision = None

def _get_capture() -> ScreenCapture:
    global _capture
    if _capture is None:
        _capture = ScreenCapture()
    return _capture

def _get_ocr() -> OCR:
    global _ocr
    if _ocr is None:
        _ocr = OCR()
    return _ocr

def _get_vision() -> VisionLLM:
    global _vision
    if _vision is None:
        _vision = VisionLLM()
    return _vision

def describe_screen() -> str:
    """
    Descreve o que está visível na tela atual usando LLaVA.
    """
    try:
        cap = _get_capture()
        vision = _get_vision()
        
        image, path = cap.capture_full(save=True)
        description = vision.describe_screen(image)
        
        return f"Descrição da tela atual:\n{description}"
    except Exception as e:
        return f"Erro ao descrever tela: {e}"

def read_screen_text() -> str:
    """
    Extrai todo o texto visível na tela usando OCR.
    """
    try:
        cap = _get_capture()
        ocr = _get_ocr()
        
        image, _ = cap.capture_full(save=False)
        text = ocr.extract_text(image)
        
        if not text:
            return "Nenhum texto legível encontrado na tela."
        
        # Limitar a 2000 caracteres
        if len(text) > 2000:
            text = text[:2000] + "\n... (texto truncado)"
        
        return f"Texto encontrado na tela:\n{text}"
    except Exception as e:
        return f"Erro ao ler texto: {e}"

def answer_about_screen(question: str) -> str:
    """
    Responde uma pergunta sobre o conteúdo da tela.
    """
    try:
        cap = _get_capture()
        vision = _get_vision()
        
        image, _ = cap.capture_full(save=False)
        answer = vision.answer_about_screen(image, question)
        
        return answer
    except Exception as e:
        return f"Erro ao responder: {e}"

def read_error_on_screen() -> str:
    """
    Detecta e descreve mensagens de erro na tela.
    """
    try:
        cap = _get_capture()
        vision = _get_vision()
        
        image, _ = cap.capture_full(save=False)
        error_desc = vision.read_error_message(image)
        
        return error_desc
    except Exception as e:
        return f"Erro ao detectar erros: {e}"

def click_on_text(target_text: str) -> str:
    """
    Clica em um elemento identificado por seu texto visível.
    """
    try:
        cap = _get_capture()
        ocr = _get_ocr()
        
        image, _ = cap.capture_full(save=False)
        location = ocr.find_text_location(image, target_text)
        
        if location is None:
            return f"Texto '{target_text}' não encontrado na tela."
        
        # Calcular centro do bounding box
        center_x = location["x"] + location["width"] // 2
        center_y = location["y"] + location["height"] // 2
        
        # Clicar
        pyautogui.click(center_x, center_y)
        time.sleep(0.5)  # Pequeno delay para GUI processar
        
        return f"Clicado em '{target_text}' na posição ({center_x}, {center_y})"
    except Exception as e:
        return f"Erro ao clicar: {e}"

def monitor_screen_change(timeout_seconds: int = 30) -> str:
    """
    Monitora a tela até detectar mudança.
    """
    try:
        cap = _get_capture()
        vision = _get_vision()
        
        initial_img, _ = cap.capture_full(save=False)
        
        start_time = time.time()
        while time.time() - start_time < timeout_seconds:
            time.sleep(2)  # Aguardar 2 segundos
            
            current_img, _ = cap.capture_full(save=False)
            diff = cap.diff_screenshots(initial_img, current_img)
            
            if diff > 5.0:  # 5% de mudança
                desc = vision.describe_screen(current_img)
                return f"Mudança detectada! {desc}"
        
        return f"Nenhuma mudança detectada em {timeout_seconds}s"
    except Exception as e:
        return f"Erro ao monitorar: {e}"