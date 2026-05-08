# jarvis/vision/monitor.py
#
# Monitor de tela em background
# Detecta mudanças visuais e notifica callbacks

import threading
import time
from jarvis.vision.capture import ScreenCapture
from jarvis import core

class ScreenMonitor:
    """
    Monitor que roda em background detectando mudanças na tela.
    """

    def __init__(self, on_change_callback, interval_seconds=5.0, diff_threshold=10.0):
        self.callback = on_change_callback
        self.interval = interval_seconds
        self.threshold = diff_threshold
        self._running = False
        self._thread = None
        self.capture = ScreenCapture()
        self._last_screenshot = None

    def start(self):
        """
        Inicia o monitoramento em background.
        """
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        core.log.info(f"Monitor de tela iniciado (intervalo: {self.interval}s, threshold: {self.threshold}%)")

    def stop(self):
        """
        Para o monitoramento.
        """
        self._running = False
        core.log.info("Monitor de tela parado")

    def _monitor_loop(self):
        """
        Loop principal do monitor.
        """
        while self._running:
            try:
                current_img, _ = self.capture.capture_full(save=False)
                
                if self._last_screenshot is not None:
                    diff = self.capture.diff_screenshots(self._last_screenshot, current_img)
                    
                    if diff > self.threshold:
                        core.log.info(f"Mudança de tela detectada: {diff:.1f}%")
                        # Executar callback em thread separada
                        threading.Thread(
                            target=self.callback,
                            args=(current_img, diff),
                            daemon=True
                        ).start()
                
                self._last_screenshot = current_img
                time.sleep(self.interval)
                
            except Exception as e:
                core.log.info(f"Erro no monitor de tela: {e}")
                time.sleep(self.interval)