# Stage 2 — Configure Local Models

Goal: Ensure Jarvis uses local models only and does not select any cloud-backed models.

Tasks:
1. Open `openjarvis/OpenJarvis/configs/openjarvis/config.toml` or the current Jarvis config and confirm the default engine is local:
   - `default = "ollama"`
   - or `default = "vllm"`
   - or use `JARVIS_LLM_ENGINE=openjarvis` with a local OpenJarvis SDK path.
2. Search config files for any cloud engine references and remove or disable them.
   - Look for `openai`, `anthropic`, `gemini`, `google`, `openrouter`, or `chatgpt`.
3. Choose a small local model that is already installed or easy to download.
   - For Ollama: `qwen3:0.6b`, `qwen3:8b`, or another local model you have pulled.
   - For vLLM: a local model path such as `/models/llama-2-7b/` or a supported file path.
   - For OpenJarvis: use a model configured via `openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml` or your own local persona.
4. Set the chosen local model as the default in Jarvis config.
   - Example: `model = "qwen3:0.6b"` for Ollama
   - Example: `model = "/path/to/local/model"` for vLLM
   - Use `JARVIS_OPENJARVIS_CONFIG` if you want Jarvis to load a custom OpenJarvis config file.
5. Ensure the active preset and CLI settings are not forcing a cloud model.
   - Check `openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml` if it is referenced.
6. Restart Jarvis or the local backend after config changes.
7. Run a quick local verification command.
   - Example: `uv run jarvis ask "What is the local model setup?"`

Verification:
- Jarvis launches with the configured local model.
- The selected model does not begin with `gpt-`, `claude-`, `gemini-`, `openrouter/`, or `chatgpt-`.
- No cloud API keys are required by the current config.
- The model remains small enough to fit a daily free-credit friendly workflow.

Notes:
- Stage 2 is about selecting and locking in a local model.
- Keep the changes explicit so the upgrade stays offline and free.
- Prefer local model names or paths that are already available on disk.
