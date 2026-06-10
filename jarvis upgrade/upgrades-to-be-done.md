# Jarvis Enhancements — Tasks to Be Done

This file lists optional improvements for the Jarvis installation after the core offline setup is complete.

Each task includes a clear description, steps to implement it, and expected outcome.

---

## 1. Install Piper Portuguese TTS Voice

**What it is:** Replace the generic pyttsx3 fallback with a high-quality Portuguese voice using Piper.

**Why it helps:** Better voice quality and natural-sounding Portuguese responses instead of the generic system voice.

**Current status:** Piper voice files missing → falls back to pyttsx3.

### How to do it

1. Download the Piper Portuguese model:
   ```powershell
   cd c:\Users\Pichau\Documents\Programming\Jarvis
   $ProgressPreference = 'SilentlyContinue'
   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx" -OutFile "jarvis\data\voices\pt_BR-faber-medium.onnx"
   Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json" -OutFile "jarvis\data\voices\pt_BR-faber-medium.onnx.json"
   ```

2. Verify the files exist:
   ```powershell
   Get-ChildItem jarvis\data\voices\pt_BR*
   ```

3. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

### Expected outcome
- Logs show: `Sintetizador usando backend piper (Piper TTS)`
- Portuguese voice responses instead of generic text-to-speech

---

## 2. Install Silero-VAD with torchaudio

**What it is:** Replace the amplitude-based voice activity detection with Silero-VAD, a more accurate ML model.

**Why it helps:** Better silence detection and more accurate command recording; cleaner transcriptions.

**Current status:** Missing torchaudio → uses amplitude fallback (less accurate).

### How to do it

1. Install torchaudio:
   ```powershell
   pip install torchaudio
   ```

2. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

3. Check logs for:
   ```
   [INFO] Silero-VAD carregado ✓
   ```

### Expected outcome
- Logs show: `Silero-VAD carregado ✓` (no warning about torchaudio)
- Cleaner audio recordings with better silence detection
- Fewer false positives in command detection

---

## 3. Connect Full LLM Backend (Ollama or OpenJarvis)

**What it is:** Enable real LLM responses instead of mock responses.

**Why it helps:** Intelligent, context-aware replies to unstructured commands.

**Current status:** LLM in MOCK mode → responds with generic "Como posso ajudar?" (How can I help?).

### How to do it (Ollama)

1. Install Ollama from [ollama.ai](https://ollama.ai)

2. Start Ollama server in a separate terminal:
   ```powershell
   ollama serve
   ```

3. Pull a small Portuguese-friendly model:
   ```powershell
   ollama pull qwen3:0.6b
   ```

4. In Jarvis config (`jarvis/config.py`), ensure:
   ```python
   LLM_ENGINE = "ollama"
   LLM_MODEL = "qwen3:0.6b"
   OLLAMA_HOST = "http://localhost:11434"
   ```

5. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

6. Check logs for:
   ```
   [INFO] Ollama disponível ✓
   ```

### Expected outcome
- Logs show: `Ollama disponível ✓` and `healthy: true`
- LLM responds with intelligent replies (no longer mock responses)
- Unstructured commands are understood and answered

---

## 4. Expand Command Registry

**What it is:** Add more voice command mappings for common tasks.

**Why it helps:** More voice commands work without needing the LLM.

**Current status:** Only a few commands mapped (chrome open/close, time, date, version).

### How to do it

1. Open `jarvis/commands/registry.py`

2. Look at the `COMMAND_PATTERNS` dictionary

3. Add new command patterns (example):
   ```python
   r'\b(abrir|abre)\s+(calculadora|calc)\b': 'open_calculator',
   r'\b(abrir|abre)\s+(notas|bloco)\b': 'open_notepad',
   r'\b(volume|som)\s+(aumentar|subir|louder)\b': 'volume_up',
   r'\b(volume|som)\s+(diminuir|baixar|lower)\b': 'volume_down',
   r'\bquantas\s+horas\b|\bque\s+horas\s+são\b': 'time',
   ```

4. Implement the handler in `jarvis/commands/handlers.py`:
   ```python
   def open_calculator():
       import subprocess
       subprocess.Popen('calc.exe')
       return True
   
   def volume_up():
       # Use pyaudio or similar
       return True
   ```

5. Test:
   ```powershell
   python jarvis.py
   # Say: "acorde" then "abrir calculadora"
   ```

### Expected outcome
- New commands work without LLM fallback
- More responsive voice control
- Faster offline command execution

---

## 5. Configure Custom Audio Device

**What it is:** Explicitly select the best microphone if multiple are detected.

**Why it helps:** Ensure consistent, high-quality audio input.

**Current status:** Auto-selected device (REDRAGON Live Camera), but may not be optimal.

### How to do it

1. Run Jarvis and note the audio device list in the logs:
   ```
   Audio input devices:
       0: Mapeador de som da Microsoft - Input
       1: Microphone (REDRAGON Live Camer...
       2: Microfone (Realtek(R) Audio)...
   ```

2. Choose the best device (e.g., device 2 = Realtek microphone)

3. Set environment variable:
   ```powershell
   $env:JARVIS_AUDIO_DEVICE = "2"
   python jarvis.py
   ```

4. If it works well, add to your terminal profile:
   ```powershell
   $env:JARVIS_AUDIO_DEVICE = "2"
   ```

### Expected outcome
- Logs show: `STATUS: Dispositivo: Microfone (Realtek(R) Audio) @ 44100Hz`
- Better audio quality and fewer background noise issues

---

## 6. Add Custom Voice Responses and Personality

**What it is:** Customize Jarvis responses to match your preferences.

**Why it helps:** More personalized, engaging interactions.

**Current status:** Generic responses ("Entendido, senhor. Como posso ajudar?").

### How to do it

1. Open `jarvis/commands/handlers.py`

2. Modify the response strings:
   ```python
   def open_chrome():
       speak("Abrindo o navegador Chrome, senhor.")  # Custom response
       # ... rest of code
   ```

3. Or edit the LLM system prompt in `jarvis/brain/brain.py`:
   ```python
   SYSTEM_PROMPT = """
   Você é JARVIS, um assistente de voz offline em português.
   Responda de forma concisa e educada.
   Sempre trate o usuário como "senhor".
   """
   ```

4. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

### Expected outcome
- Personalized voice responses
- More natural and engaging interactions
- Custom greetings and closings

---

## 7. Enable HUD Customization (Theme/Colors)

**What it is:** Customize the visual overlay appearance.

**Why it helps:** Better visibility or aesthetic preferences.

**Current status:** Default dark theme.

### How to do it

1. Open `jarvis/hud/theme.py`

2. Modify color values:
   ```python
   # Example: Change background color
   COLORS = {
       "bg_dark": "#1a1a2e",  # Background
       "accent": "#00d4ff",   # Accent color
       "text": "#ffffff",     # Text color
   }
   ```

3. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

### Expected outcome
- Custom HUD appearance
- Better visual feedback based on your preferences

---

## 8. Add Scheduled Tasks / Automation

**What it is:** Create periodic tasks that Jarvis executes automatically.

**Why it helps:** Automated reminders, health checks, and maintenance.

**Current status:** Scheduler available but no tasks configured.

### How to do it

1. Open `jarvis/brain/scheduler.py`

2. Add a scheduled task (example: hourly time check):
   ```python
   def hourly_check():
       speak("Hora de checar as atualizações, senhor.")
   
   scheduler.add_job(hourly_check, 'interval', hours=1, id='hourly_check')
   ```

3. Restart Jarvis:
   ```powershell
   python jarvis.py
   ```

### Expected outcome
- Periodic tasks execute automatically
- Better time management and reminders

---

## 9. Enable Local Document/File Search

**What it is:** Allow Jarvis to search and open files locally.

**Why it helps:** "Find my document" type commands without cloud search.

**Current status:** Basic file tools available but not well integrated with voice.

### How to do it

1. Open `jarvis/tools/files.py`

2. Add a voice-friendly search function:
   ```python
   def search_files(keyword):
       # Search local directories for matching files
       pass
   ```

3. Register it in `jarvis/commands/handlers.py`:
   ```python
   r'\b(procurar|find)\s+(arquivo|file)\s+(.+)\b': 'search_file',
   ```

### Expected outcome
- Voice commands like "procurar documento sobre vendas"
- Quick file location and opening

---

## 10. Run System Health Check

**What it is:** Verify all local components are working correctly.

**Why it helps:** Early detection of missing or broken dependencies.

### How to do it

1. Run the built-in doctor command:
   ```powershell
   python jarvis.py doctor
   ```

2. Review output for any `false` or `null` values

3. Fix any issues (e.g., missing models)

### Expected outcome
- All components show healthy status
- Confidence that the system is fully operational

---

## Summary

| Task | Priority | Time | Difficulty |
|------|----------|------|------------|
| 1. Piper TTS | Medium | 5 min | Easy |
| 2. Silero-VAD | Low | 2 min | Easy |
| 3. LLM Backend | High | 15 min | Medium |
| 4. Command Registry | Medium | 30 min | Medium |
| 5. Audio Device | Low | 10 min | Easy |
| 6. Custom Responses | Low | 15 min | Easy |
| 7. HUD Customization | Low | 20 min | Easy |
| 8. Scheduled Tasks | Low | 20 min | Medium |
| 9. File Search | Medium | 30 min | Hard |
| 10. Health Check | High | 2 min | Easy |

**Recommended order:**
1. Run health check (Task 10) — verify current state
2. Connect LLM (Task 3) — enable intelligent responses
3. Install Piper TTS (Task 1) — better voice quality
4. Expand commands (Task 4) — more offline functionality
5. Others as desired

---

## Testing Each Enhancement

After each task, test by running:
```powershell
python jarvis.py doctor
```

Then start Jarvis:
```powershell
python jarvis.py
```

And say: **"acorde"** followed by a test command.

---
