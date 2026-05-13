# JARVIS HUD

JARVIS HUD é um assistente de voz offline em Python, inspirado no Jarvis de Tony Stark. O projeto combina:

- detecção de palavra-chave com Vosk
- detecção de silêncio com Silero VAD
- transcrição local com `faster-whisper`
- síntese de voz com `pyttsx3`
- interface HUD com Tkinter
- integração local com motores de inferência LLM via Ollama ou OpenJarvis

O foco principal é rodar sem dependência de APIs pagas ou serviços em nuvem, usando apenas recursos gratuitos e modelos locais.

---

## 🚀 O que este projeto faz

- ativa escuta por voz quando você diz a palavra de ativação (`acorde` por padrão)
- grava a fala até identificar silêncio e envia para transcrição local
- converte áudio em texto via Whisper local
- processa comandos e responde com voz ou texto
- exibe um overlay gráfico com status, histórico e mensagens
- oferece um backend de LLM local que pode usar `ollama` ou o código `openjarvis` integrado

---

## 📁 Estrutura do repositório

```
.jarvis/              # pacote principal do assistente
  commands/           # implementa comandos e registro de handlers
  brain/              # lógica do LLM e integração com OpenJarvis/Ollama
  hud/                # renderização do overlay e widgets
  voice/              # wake-word, VAD, gravação e transcrição
  config.py           # configurações e variáveis ambientais
  core.py             # logging, eventos e utilitários
  main.py             # ponto de entrada da aplicação

jarvis_hud.py         # launcher primário que inicia o HUD
requeriments.txt      # dependências Python necessárias
models/               # modelos de voz e arquivos locais
openjarvis/           # fonte do OpenJarvis integrada ao projeto
jarvis upgrade/       # etapas de configuração para uso local/offline
scripts/              # utilitários de download e suporte
README.md             # documentação do projeto
```

---

## 🛠️ Requisitos

- Python 3.10 ou superior
- `pip` instalado
- ambiente virtual recomendado
- modelo Vosk em `models/vosk-pt`
- modelo Whisper local em `models/whisper-small` para operação offline completa

### Instalação de dependências

```sh
python -m pip install -r requeriments.txt
```

Dependências principais:

- `faster-whisper`
- `numpy`
- `psutil`
- `pyttsx3`
- `scipy`
- `silero-vad`
- `sounddevice`
- `torch`
- `vosk`

> `psutil` ajuda no monitoramento de recursos; `torch` e `faster-whisper` fazem a transcrição local.

---

## 🧩 Configuração inicial

1. Clone o repositório:
   ```sh
git clone <repo-url> jarvis
cd jarvis
```
2. Crie e ative um ambiente virtual:
   ```sh
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```
3. Instale as dependências:
   ```sh
pip install -r requeriments.txt
```
4. Baixe e extraia o modelo Vosk em `models/vosk-pt`.
5. Baixe o modelo Whisper local usando o script ou copie um modelo local para `models/whisper-small`.
6. Se desejar, configure um backend local Ollama ou OpenJarvis para respostas mais inteligentes.

---

## ▶️ Como executar

Para iniciar o HUD:

```sh
python jarvis_hud.py
```

Ou execute o módulo principal:

```sh
python -m jarvis.main
```

O projeto abrirá um overlay transparente com informações de status. Diga `acorde` (ou a palavra definida em `config.py` / `WAKE_WORD`) e, após o prompt de confirmação, fale o seu comando.

---

## 🧠 Configurações importantes

### `jarvis/config.py`

Principais variáveis:

- `WAKE_WORD` — palavra de ativação usada pelo wake-word
- `JARVIS_AUDIO_DEVICE` — dispositivo de entrada de áudio opcional
- `WHISPER_MODEL` — modelo local de ASR (detecta `models/whisper-small/model.bin` automaticamente)
- `LLM_MODEL` — modelo padrão para a integração de inferência local
- `LLM_ENGINE` — engine atual para LLM local (`ollama` por padrão)
- `OLLAMA_HOST` — URL do servidor Ollama local
- `JARVIS_OPENJARVIS_PATH` — caminho para a fonte OpenJarvis no repositório
- `JARVIS_OPENJARVIS_CONFIG` — caminho opcional para um arquivo de configuração OpenJarvis

### Variáveis de ambiente úteis

* `JARVIS_AUDIO_DEVICE` — índice ou parte do nome do microfone
* `WAKE_WORD` — palavra de ativação para iniciar o assistente
* `JARVIS_LLM_ENGINE` — engine local de inferência:
  - `ollama` (padrão)
  - `openjarvis` (usa `openjarvis/OpenJarvis/src`)
* `JARVIS_OPENJARVIS_PATH` — caminho para o SDK OpenJarvis local
* `JARVIS_OPENJARVIS_CONFIG` — arquivo de configuração OpenJarvis opcional
* `OLLAMA_HOST` — URL do Ollama local, padrão `http://localhost:11434`

---

## 🔧 OpenJarvis e inferência local

O projeto suporta dois modos principais de LLM local:

1. **Ollama**
   - execute `ollama serve` e use um modelo local como `qwen3:0.6b`
   - o Jarvis se conecta via `OLLAMA_HOST`
2. **OpenJarvis**
   - use o SDK local em `openjarvis/OpenJarvis/src`
   - configure `JARVIS_LLM_ENGINE=openjarvis`
   - opcionalmente use `JARVIS_OPENJARVIS_CONFIG` para apontar para um arquivo de configuração OpenJarvis

Essas opções permitem manter o projeto no modo offline e evitar serviços pagos.

---

## 📦 Desenvolvimento e personalização

### Adicionar novos comandos

- edite `jarvis/commands/handlers.py`
- registre comandos em `jarvis/commands/registry.py`
- implemente lógica adicional em `jarvis/core.py` ou `jarvis/main.py`

### Personalizar a interface HUD

- `jarvis/hud/renderer.py` controla o desenho do overlay
- `jarvis/hud/widgets.py` define os elementos visuais
- `jarvis/hud/theme.py` define cores e estilos

### Ajustar reconhecimento de voz

- `jarvis/voice/wake_word.py` gerencia a detecção da palavra-chave
- `jarvis/voice/vad.py` controla o corte de silêncio e gravação
- `jarvis/voice/transcriber.py` faz a transcrição local com Whisper

---

## 📝 Logs e depuração

O sistema registra atividades em `jarvis.log` com rotação de arquivos (5 MB × 3 backups).
Use o log para diagnosticar:

- falhas de áudio
- problemas de transcrição
- falha de inicialização do HUD
- problemas de conexão ao motor LLM local

---

## 🔒 Como garantir operação 100% offline

Para rodar sem qualquer dependência de Hugging Face ou internet:

1. Baixe o modelo Whisper localmente para `models/whisper-small`.
2. Configure `JARVIS_WHISPER_DIR` se usar outro caminho.
3. Não defina chaves de API em variáveis de ambiente.
4. Use `ollama` ou `openjarvis` como backend local em vez de provedores em nuvem.

### Exemplo PowerShell

```powershell
$env:JARVIS_WHISPER_DIR = "models/whisper-small"
$env:JARVIS_LLM_ENGINE = "ollama"
$env:OLLAMA_HOST = "http://localhost:11434"
python jarvis_hud.py
```

---

## ✅ Próximos passos

1. Leia as etapas em `jarvis upgrade/` para configurar o projeto para operação local e offline.
2. Configure um backend Ollama ou OpenJarvis e teste com um modelo pequeno como `qwen3:0.6b`.
3. Personalize comandos e a interface HUD para o seu fluxo de trabalho.
4. Adicione suporte a mais idiomas, vozes e comandos de automação local.
5. Crie testes automatizados e adicione validações de configuração no `jarvis` package.
6. Mantenha o projeto offline revisando `config.py` e removendo quaisquer referências a APIs em nuvem.

---

## 📜 Licença

Este projeto usa dependências gratuitas e código open-source. O repositório não possui uma licença explícita definida no arquivo principal.

---

*Desenvolvido com ❤️ em Python para um assistente de voz local e personalizável.*
