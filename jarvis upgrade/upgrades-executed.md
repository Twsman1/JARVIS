# Jarvis Offline Upgrade Guide

This single guide combines all offline upgrade stages for the Jarvis repository.
It is designed to be easy to follow and focused on keeping Jarvis fully local, free, and cloud-free.

## Overview

The offline upgrade process has six practical stages:
1. Setup a local inference backend
2. Configure local models
3. Apply a local agent preset
4. Install and verify offline skills/tools
5. Validate no-cloud operation
6. Maintain and upgrade the local Jarvis setup

Use this guide as the one stop reference for the `jarvis upgrade` workflow.

---

## 1. Setup Local Inference Backend

Goal: Configure Jarvis to use a local LLM backend only and avoid any cloud API calls.

### What to do
- Choose one local backend:
  - preferred: `ollama`
  - alternative: `vllm`
  - optional: OpenJarvis engine integration using the embedded OpenJarvis SDK
- Disable any cloud API keys in the current shell:
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GEMINI_API_KEY`
  - `GOOGLE_API_KEY`
  - `OPENROUTER_API_KEY`
- Install and start the chosen backend.

### Local backend examples
- Ollama:
  ```powershell
  ollama serve &
  ollama pull qwen3:0.6b
  ```
- OpenJarvis engine integration:
  ```powershell
  set JARVIS_LLM_ENGINE=openjarvis
  set JARVIS_OPENJARVIS_PATH=openjarvis/OpenJarvis/src
  set JARVIS_OPENJARVIS_CONFIG=openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml
  ```
- vLLM:
  ```powershell
  vllm start --model C:\path\to\local\model
  ```

### Recommended model
- Use a small starter model, for example: `qwen3:0.6b`
- Avoid very large models during this initial upgrade stage.

### Configure Jarvis
- Update `jarvis/config.py` if needed:
  - `LLM_ENGINE = "ollama"` or `LLM_ENGINE = "openjarvis"`
  - `JARVIS_OPENJARVIS_PATH` and `JARVIS_OPENJARVIS_CONFIG` for OpenJarvis

### Verify
- Start Jarvis and confirm it uses local inference only.
- Check logs for any cloud references such as `cloud`, `openai`, `anthropic`, `gemini`, or `google`.

---

## 2. Configure Local Models

Goal: Lock Jarvis to local models only and remove any cloud-backed model references.

### What to do
- Open and inspect config files:
  - `openjarvis/OpenJarvis/configs/openjarvis/config.toml`
  - `openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml`
  - `jarvis/config.py`
- Confirm the default engine is local-friendly:
  - `default = "ollama"`
  - `default = "vllm"`
  - or use `JARVIS_LLM_ENGINE=openjarvis`
- Remove cloud engine references:
  - `openai`
  - `anthropic`
  - `gemini`
  - `google`
  - `openrouter`
  - `chatgpt`

### Choose a local model
- For Ollama: `qwen3:0.6b`, `qwen3:8b`, or another already-installed local model
- For vLLM: a local model path like `C:\models\llama-2-7b\`
- For OpenJarvis: use a local preset such as `chat-simple.toml`

### Set the model
- Example in Jarvis config:
  - `model = "qwen3:0.6b"` for Ollama
  - `model = "C:\path\to\local\model"` for vLLM
- Use `JARVIS_OPENJARVIS_CONFIG` for custom OpenJarvis configs.

### Verify
- Restart Jarvis after config changes.
- Confirm the selected model does not start with any forbidden cloud prefix.
- Ensure no cloud API keys are required by the current config.

---

## 3. Setup Local Agent Presets

Goal: Initialize Jarvis with a preset that works offline and uses local inference.

### What to do
- Review available local-friendly presets in `openjarvis/OpenJarvis/README.md`.
- Prefer local-first presets such as `chat-simple`.
- Initialize Jarvis with the chosen preset.

### Commands
- If `uv` is available:
  ```powershell
  uv run jarvis init --preset chat-simple
  ```
- If `uv` is unavailable, set:
  ```powershell
  set JARVIS_OPENJARVIS_CONFIG=openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml
  ```
  and start Jarvis normally.

### Verify
- Jarvis starts with the preset successfully.
- The preset does not require OAuth cloud connectors or paid APIs.
- The agent uses local inference for responses.

---

## 4. Install Free Offline Skills and Tools

Goal: Add offline functionality without introducing cloud or paid dependencies.

### What to do
- Keep Jarvis local-only:
  - `JARVIS_LLM_ENGINE=openjarvis` or `JARVIS_LLM_ENGINE=ollama`
  - `JARVIS_OPENJARVIS_CONFIG=openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml`
- Verify ASR and TTS are local:
  - `JARVIS_WHISPER_DIR` should point to `models/whisper-small`
  - local TTS data is already at `jarvis/data/voices/pt_BR-faber-medium.onnx`
- Avoid cloud-only connectors and paid tool integrations.

### Why this matters
- Jarvis does not currently have a dynamic cloud skill store in this repo.
- Offline power comes from local deterministic commands, local LLM, local Whisper ASR, and local TTS.

### Verify
- Jarvis launches using local LLM inference and local Whisper ASR.
- No cloud downloads are attempted by default.
- No cloud API keys are required.
- Offline deterministic commands should work without LLM fallback.

---

## 5. Validate Offline No-Cloud Operation

Goal: Confirm the entire setup is fully offline and free of cloud dependencies.

### What to do
- Run a simple local query:
  ```powershell
  uv run jarvis ask "Hello, Jarvis. Tell me a short summary of the local setup."
  ```
- Check engine and model output.
- Verify startup logs contain no cloud backends.
- Confirm environment variables do not include cloud API keys.
- If any cloud dependency appears, revert to local settings.

### Important note
- Local Whisper discovery now supports nested Hugging Face cache snapshot paths.
- `JARVIS_WHISPER_DIR` can resolve `model.bin` inside cached directories.

### Verify
- Jarvis responds using local inference.
- No cloud API keys are required or referenced.
- The system remains usable without internet access for inference.

---

## 6. Maintain and Upgrade Local Jarvis

Goal: Keep the Jarvis installation local, healthy, and up to date.

### Maintenance checklist
1. Update local models safely
   - Ollama: `ollama pull <model>` and `ollama list`
   - OpenJarvis: refresh local weights or replace model files
   - Whisper: ensure `JARVIS_WHISPER_DIR` still points to a directory containing `model.bin`
2. Keep Jarvis local-only
   - avoid `cloud` engine settings
   - keep cloud API keys unset
   - avoid `gpt-`, `claude-`, `gemini-`, `openrouter/`, `chatgpt-` model names
3. Check system health
   - run:
     ```powershell
     python jarvis.py doctor
     ```
   - for Ollama: `curl http://localhost:11434/api/tags`
   - for OpenJarvis: verify the configured preset and model health
4. Review config periodically
   - `openjarvis/OpenJarvis/configs/openjarvis/config.toml`
   - `openjarvis/OpenJarvis/configs/openjarvis/examples/`
   - `jarvis/config.py`

### What maintenance does not require
- no cloud API key setup
- no cloud service restart
- no remote inference or online Whisper fallback
- no `openai`, `anthropic`, `google`, `openrouter`, or other cloud provider keys

### Verify
- local CLI diagnostics run cleanly
- no cloud settings are reintroduced
- the project remains offline and free by design

---

## Quick verification commands

```powershell
python jarvis.py doctor
python jarvis.py
python -m jarvis.main
```

Use `python jarvis.py doctor` as the local health check for this repository.

---

## Notes
- This consolidated guide is the recommended single reference for the Jarvis offline upgrade.
- Follow the stages in order: backend, models, preset, skills/tools, validation, maintenance.
- Keep the setup explicit and local so the project stays free and cloud-independent.
