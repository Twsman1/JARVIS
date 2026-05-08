# jarvis/brain/task_detector.py
#
# Detector de tarefas complexas vs simples
# Decide se usar Agent (ReAct loop) ou Brain simples

# Indicadores de tarefa complexa (múltiplas ações)
COMPLEX_INDICATORS = [
    " e depois ", " e então ", " em seguida ", " após isso ",
    " e salve ", " e escreva ", " e abra ", " e feche ",
    " e pesquise ", " e busque ", " e crie ", " e cole ",
    " depois de ", " ao terminar ", " quando acabar ",
]

# Indicadores de tarefa simples (resposta direta)
SIMPLE_INDICATORS = [
    "qual é", "quem é", "quando foi", "onde fica", "como se",
    "o que é", "me explique", "me conte", "me diga",
    "obrigado", "valeu", "boa tarde", "bom dia", "boa noite",
    "olá", "oi jarvis", "tudo bem",
]

def is_complex_task(text: str) -> bool:
    """
    Determina se uma tarefa é complexa (requer Agent) ou simples (Brain basta).

    Args:
        text: Comando do usuário (será convertido para lowercase)

    Returns:
        True se deve usar Agent, False se Brain simples basta
    """
    text_lower = text.lower().strip()

    # 1. Verificar indicadores de tarefa simples
    for indicator in SIMPLE_INDICATORS:
        if indicator in text_lower:
            return False

    # 2. Verificar indicadores de tarefa complexa
    for indicator in COMPLEX_INDICATORS:
        if indicator in text_lower:
            return True

    # 3. Contar verbos de ação na frase
    action_verbs = [
        "abr", "fech", "pesquis", "busqu", "salv", "cri", "escrev",
        "digit", "copi", "mov", "delet", "execut", "ligu", "desligu",
        "instal", "remov", "atualiz", "baix", "carreg", "envi", "mand",
        "proc", "encontr", "localiz", "acess", "naveg", "abr", "inic",
        "par", "paus", "reinici", "reinicializ", "config", "ajust"
    ]

    verb_count = 0
    words = text_lower.split()
    for word in words:
        for verb in action_verbs:
            if verb in word:
                verb_count += 1
                break

    # Se tem 2 ou mais verbos de ação, provavelmente é complexa
    if verb_count >= 2:
        return True

    # 4. Verificar comprimento + presença de verbos
    word_count = len(words)
    has_action_verb = verb_count > 0

    # Tarefa longa (>15 palavras) com verbo de ação é provavelmente complexa
    if word_count > 15 and has_action_verb:
        return True

    # 5. Default: tarefa simples
    return False