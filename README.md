# JARVIS HUD

JARVIS HUD é um assistente pessoal de voz totalmente offline inspirado no Jarvis de Tony Stark. Ele combina reconhecimento de palavra-chave (wake word), detecção de silêncio (VAD) e transcrição com `faster-whisper`, exibindo um overlay gráfico com status e histórico de comandos. O projeto foi escrito em Python e utiliza apenas dependências gratuitas.

---

## 🚀 Funcionalidades principais

- Detecção de palavra-chave com Vosk (`acorde` por padrão)
- Gravação e filtragem de comando usando Silero VAD
- Transcrição de comandos em português (pt-BR) via [faster-whisper](https://github.com/guillaumekln/faster-whisper)
- Síntese de voz com `pyttsx3` (sistema) e escolha de voz automática
- Interface HUD com Tkinter exibindo status, volume e histórico
- Registro de eventos em arquivo com rotação (RotatingFileHandler)
- Estrutura modular (`jarvis` package) para fácil manutenção e extensão

> 🧠 Modo offline completo. Nenhuma chamada para APIs externas.

---

## 📁 Estrutura do projeto

```
jarvis/              # pacote principal
  commands/          # manipuladores de comando e registro
  hud/               # renderizador de overlay e tema
  voice/             # wake-word, VAD e transcrição
  config.py          # constantes de configuração
  core.py            # logging, eventos e utilitários
  main.py            # ponto de entrada da aplicação

jarvis_hud.py        # launcher (importa jarvis.main)
requeriments.txt     # dependências Python
models/              # modelos Vosk e outros recursos de voz
```

---

## 🛠️ Requisitos

* Python 3.10+ (usuário usou 3.13) – recomendável criar um virtualenv
* `pip` disponível
* Modelos de voz:
  * Baixe [vosk-model-small-pt-0.3](https://alphacephei.com/vosk/models) e extraia para `models/vosk-pt`

### Dependências Python

Instale com:

```sh
python -m pip install -r requeriments.txt
```

O arquivo contém:

```
faster-whisper
numpy
psutil
pyttsx3
scipy
silero-vad
sounddevice
torch
vosk
```

> 🔧 `psutil` é usado para monitoramento de recursos; `torch` e `faster-whisper` fazem o trabalho de ASR.

---

## 🧩 Instalação

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
3. Instale requisitos:
   ```sh
pip install -r requeriments.txt
```
4. Baixe e posicione o modelo Vosk, como mencionado acima.
5. (Opcional) instale vozes adicionais no sistema para customizar a voz TTS.

---

## ▶️ Uso

Execute:

```sh
python jarvis_hud.py
```

ou diretamente via módulo:

```sh
python -m jarvis.main
```

O aplicativo abrirá uma janela transparente com informações de status. Diga `acorde` (ou palavra definida em `config.py`/variável de ambiente `WAKE_WORD`) para ativar o modo de comando. Após ouvir o "Sim, senhor?" fale um comando.

### Variáveis de ambiente úteis

* `JARVIS_AUDIO_DEVICE` – índice ou parte do nome para escolher dispositivo de entrada
* `WAKE_WORD` – palavra de ativação (pode ser alterada em `config.py`)

---

## 🧠 Adaptação e personalização

- Edite `config.py` para ajustar parâmetros de VAD, modelo Whisper, etc.
- Adicione comandos em `jarvis/commands/handlers.py` e atualize `registry.py`.
- Personalize a GUI em `jarvis/hud/renderer.py` e `theme.py`.
- A lógica de reconhecimento de voz está em `jarvis/voice/wake_word.py`.

---

## 📝 Logs e depuração

Mensagens são gravadas em `jarvis.log` (5 MB × 3 backups). Consulte o log para
problemas de áudio, transcrição ou configuração.

---

## ✅ Possíveis melhorias

* Suporte a plugins/skills
* Interface de configuração via arquivo ou GUI
* Testes automatizados e CI
* Suporte a outros idiomas/vozes
* Integração com serviços locais de LLM para respostas mais inteligentes

---

## 📜 Licença

Este projeto usa apenas dependências gratuitas/open-source. O código em si não tem
licença especificada aqui;


---

*Desenvolvido com ❤️ por Lino, inspirado no universo Marvel.*
