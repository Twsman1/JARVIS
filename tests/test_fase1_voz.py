# tests/test_fase1_voz.py
#
# COPILOT: Implemente este arquivo de testes completo.
# Cada função test_* é um teste independente.
# Use assert para validar resultados.
# Capture exceções e forneça mensagens de erro claras.

import pytest
import numpy as np
import time
import threading


# ── TESTES DO RECORDER ────────────────────────────────────────────────────────

def test_recorder_importa():
    """Verifica se o módulo recorder importa sem erros."""
    from jarvis.voice.recorder import AudioRecorder, SAMPLE_RATE
    assert SAMPLE_RATE == 16000

def test_recorder_instancia():
    """Verifica se AudioRecorder instancia sem erros."""
    from jarvis.voice.recorder import AudioRecorder
    r = AudioRecorder(vad_aggressiveness=2)
    assert r is not None

def test_recorder_captura_audio():
    """
    COPILOT: Implemente este teste.
    - Instanciar AudioRecorder
    - Iniciar gravação em thread separada com timeout de 10 segundos
    - Verificar que o retorno é numpy array com dtype int16
    NOTA: Pode falhar se não houver microfone disponível.
    """
    from jarvis.voice.recorder import AudioRecorder
    r = AudioRecorder()
    resultado = {"audio": None, "erro": None}

    def gravar():
        try:
            audio = r.record()
            resultado["audio"] = audio
        except Exception as e:
            resultado["erro"] = str(e)

    t = threading.Thread(target=gravar, daemon=True)
    t.start()
    t.join(timeout=10)

    assert resultado["erro"] is None, f"Erro na gravação: {resultado['erro']}"
    assert resultado["audio"] is not None, "Nenhum áudio retornado"
    assert isinstance(resultado["audio"], np.ndarray), "Retorno não é numpy array"
    assert resultado["audio"].dtype == np.int16, "dtype incorreto (deve ser int16)"


# ── TESTES DO TRANSCRIBER ─────────────────────────────────────────────────────

def test_transcriber_importa():
    """Verifica se o módulo transcriber importa sem erros."""
    from jarvis.voice.transcriber import Transcriber
    assert Transcriber is not None

def test_transcriber_instancia():
    """
    COPILOT: Verifica se Transcriber carrega o modelo sem erros.
    Pode demorar até 60 segundos no primeiro uso (download automático).
    """
    from jarvis.voice.transcriber import Transcriber
    t = Transcriber(model_size="base")
    assert t is not None

@pytest.mark.timeout(60)
def test_transcriber_audio_silencio():
    """
    COPILOT: Verifica que transcrever silêncio retorna string vazia ou muito curta.
    - Criar array numpy de zeros (3 segundos de silêncio puro)
    - Transcrever — resultado deve ser string com menos de 50 chars
    """
    from jarvis.voice.transcriber import Transcriber
    t = Transcriber(model_size="base")
    silencio = np.zeros(16000 * 3, dtype=np.int16)
    resultado = t.transcribe(silencio)
    assert isinstance(resultado, str), "Resultado deve ser string"
    assert len(resultado) < 50, f"Silêncio gerou texto inesperado: '{resultado}'"


# ── TESTES DO SYNTHESIZER ─────────────────────────────────────────────────────

def test_synthesizer_importa():
    """Verifica se o módulo synthesizer importa sem erros."""
    from jarvis.voice.synthesizer import Synthesizer
    assert Synthesizer is not None

def test_synthesizer_modelo_existe():
    """
    COPILOT: Verifica se os arquivos de modelo Piper existem em disco.
    """
    from pathlib import Path
    modelo = Path("jarvis/data/voices/pt_BR-faber-medium.onnx")
    config = Path("jarvis/data/voices/pt_BR-faber-medium.onnx.json")
    assert modelo.exists(), f"Modelo Piper não encontrado: {modelo}"
    assert config.exists(), f"Config Piper não encontrado: {config}"

def test_synthesizer_instancia_e_inicia():
    """Verifica se Synthesizer instancia e inicia thread daemon sem erros."""
    from jarvis.voice.synthesizer import Synthesizer
    from jarvis import core
    s = Synthesizer()
    s.start()
    time.sleep(0.5)
    core._tts_queue.put(None)
    time.sleep(0.5)

def test_synthesizer_fala():
    """
    COPILOT: Verifica que o Synthesizer processa texto sem lançar exceção.
    - Instanciar, iniciar, enfileirar texto curto, aguardar 5s.
    """
    from jarvis.voice.synthesizer import Synthesizer
    from jarvis import core
    s = Synthesizer()
    s.start()
    core.speak("teste")
    time.sleep(5)
    core._tts_queue.put(None)


# ── TESTES DO PIPELINE ────────────────────────────────────────────────────────

def test_pipeline_importa():
    """Verifica se o pipeline importa sem erros."""
    from jarvis.voice.pipeline import VoicePipeline
    assert VoicePipeline is not None

def test_pipeline_instancia():
    """
    COPILOT: Verifica que VoicePipeline instancia com callback.
    - Criar callback mock e instanciar VoicePipeline
    - Verificar atributos: recorder, transcriber, wake_listener, _processing
    """
    from jarvis.voice.pipeline import VoicePipeline
    chamadas = []
    pipeline = VoicePipeline(on_command_callback=lambda t: chamadas.append(t))
    assert pipeline.recorder is not None
    assert pipeline.transcriber is not None
    assert pipeline._processing == False