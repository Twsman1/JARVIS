# jarvis/vision/capture.py
#
# Módulo de captura de tela
# Suporta tela inteira, janela ativa, região específica e stream

import pyautogui
from PIL import Image
import numpy as np
import time
from pathlib import Path
from jarvis import core

SCREENSHOTS_DIR = Path("jarvis/data/screenshots")

class ScreenCapture:
    """
    Captura de screenshots com múltiplas opções.
    """

    def __init__(self):
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        core.log.info("Módulo de captura de tela inicializado")

    def capture_full(self, save: bool = True) -> tuple[Image.Image, str | None]:
        """
        Captura a tela inteira.
        
        Returns:
            (PIL Image, filepath string or None)
        """
        img = pyautogui.screenshot()
        filepath = None
        
        if save:
            timestamp = int(time.time())
            filepath = str(SCREENSHOTS_DIR / f"screen_{timestamp}.png")
            img.save(filepath)
            core.log.info(f"Screenshot salvo: {filepath}")
        
        return img, filepath

    def capture_region(self, x: int, y: int, width: int, height: int,
                       save: bool = True) -> tuple[Image.Image, str | None]:
        """
        Captura uma região específica da tela.
        """
        img = pyautogui.screenshot(region=(x, y, width, height))
        filepath = None
        
        if save:
            timestamp = int(time.time())
            filepath = str(SCREENSHOTS_DIR / f"screen_{timestamp}_region.png")
            img.save(filepath)
        
        return img, filepath

    def capture_active_window(self, save: bool = True) -> tuple[Image.Image, str | None]:
        """
        Captura a janela ativa.
        Falls back to full screen if window cannot be determined.
        """
        try:
            import pygetwindow
            window = pygetwindow.getActiveWindow()
            if window:
                return self.capture_region(window.left, window.top, 
                                          window.width, window.height, save=save)
        except Exception as e:
            core.log.info(f"Não foi possível obter janela ativa: {e}")
        
        return self.capture_full(save=save)

    def image_to_base64(self, image: Image.Image) -> str:
        """
        Converte PIL Image para base64 string.
        """
        from io import BytesIO
        import base64
        
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')

    def get_screen_size(self) -> tuple[int, int]:
        """
        Retorna o tamanho da tela principal (width, height).
        """
        size = pyautogui.size()
        return size

    def diff_screenshots(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        Calcula a diferença percentual entre duas screenshots.
        
        Returns:
            float: diff percentage (0.0 = identical, 100.0 = completely different)
        """
        # Converter para numpy arrays e escala de cinza
        arr1 = np.array(img1.convert('L'), dtype=np.float32)
        arr2 = np.array(img2.convert('L'), dtype=np.float32)
        
        # Redimensionar se necessário
        if arr1.shape != arr2.shape:
            arr2 = np.resize(arr2, arr1.shape)
        
        # Calcular diferença média absoluta
        diff = np.mean(np.abs(arr1 - arr2))
        
        # Normalizar para 0-100
        percentage = (diff / 255.0) * 100.0
        
        return percentage