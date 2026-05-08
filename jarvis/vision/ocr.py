# jarvis/vision/ocr.py
#
# Módulo de OCR com Tesseract
# Extrai texto de imagens com pré-processamento

import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
import numpy as np
from jarvis import core

# Configurar path do Tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class OCR:
    """
    OCR usando Tesseract com pré-processamento de imagem.
    """

    def __init__(self):
        try:
            version = pytesseract.get_tesseract_version()
            core.log.info(f"Tesseract OCR disponível: {version}")
        except Exception as e:
            core.log.info(f"ERRO: Tesseract não encontrado!")
            core.log.info(f"Instale de: https://github.com/UB-Mannheim/tesseract/wiki")
            core.log.info(f"Verifique se está em: C:\\Program Files\\Tesseract-OCR\\")

    def extract_text(self, image: Image.Image, language: str = "por+eng") -> str:
        """
        Extrai texto de uma imagem.
        """
        try:
            processed = self._preprocess(image)
            text = pytesseract.image_to_string(processed, lang=language)
            
            # Limpar linhas vazias extras
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            clean_text = '\n'.join(lines)
            
            core.log.info(f"OCR extraiu {len(clean_text)} caracteres")
            return clean_text
        except Exception as e:
            core.log.info(f"Erro na extração de texto: {e}")
            return ""

    def extract_text_from_file(self, image_path: str, language: str = "por+eng") -> str:
        """
        Extrai texto de um arquivo de imagem.
        """
        try:
            image = Image.open(image_path)
            return self.extract_text(image, language)
        except Exception as e:
            core.log.info(f"Erro ao ler arquivo {image_path}: {e}")
            return ""

    def find_text_location(self, image: Image.Image, target_text: str) -> dict | None:
        """
        Encontra a localização de um texto na imagem.
        
        Returns:
            {"x": int, "y": int, "width": int, "height": int} ou None
        """
        try:
            processed = self._preprocess(image)
            data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
            
            target_lower = target_text.lower()
            
            for i, text in enumerate(data['text']):
                if text and target_lower in text.lower():
                    return {
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i]
                    }
            
            return None
        except Exception as e:
            core.log.info(f"Erro ao procurar texto: {e}")
            return None

    def _preprocess(self, image: Image.Image) -> Image.Image:
        """
        Pré-processa a imagem para melhorar OCR.
        """
        # 1. Converter para escala de cinza
        img = image.convert('L')
        
        # 2. Aumentar contraste
        img = ImageEnhance.Contrast(img).enhance(2.0)
        
        # 3. Aumentar sharpness
        img = ImageEnhance.Sharpness(img).enhance(2.0)
        
        # 4. Redimensionar se pequena
        if img.width < 1000:
            new_size = (img.width * 2, img.height * 2)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # 5. Aplicar threshold para binarizar
        img_np = np.array(img)
        threshold = 128
        img_np[img_np < threshold] = 0
        img_np[img_np >= threshold] = 255
        img = Image.fromarray(img_np.astype(np.uint8))
        
        return img