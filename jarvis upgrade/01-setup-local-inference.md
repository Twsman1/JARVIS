# Stage 1 — Setup Local Inference Backend

Goal: Configure Jarvis to use local inference only, without any cloud API calls or paid services.

Tasks:
1. Inspect `openjarvis/OpenJarvis/deploy/docker/docker-compose.yml` and `openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml` to confirm the default engine is local-friendly.
   - Look for entries like `ollama`, `vllm`, or local-only presets and no default cloud provider.
2. Choose a local inference backend:
   - Preferred: `ollama`
   - Alternative: `vllm`
   - Optional: `openjarvis` engine integration using the OpenJarvis SDK source tree.
3. Remove or disable any cloud API key environment variables for this terminal session:
   - `OPENAI_API_KEY`
   - `ANTHROPIC_API_KEY`
   - `GEMINI_API_KEY`
   - `GOOGLE_API_KEY`
   - `OPENROUTER_API_KEY`
4. Install and configure the chosen backend.
   - For Ollama:
     ```bash
     ollama serve &
     ollama pull qwen3:0.6b
     ```
   - For openjarvis engine integration:
     ```bash
     set JARVIS_LLM_ENGINE=openjarvis
     set JARVIS_OPENJARVIS_PATH=openjarvis/OpenJarvis/src
     set JARVIS_OPENJARVIS_CONFIG=openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml
     ```
   - For vLLM:
     ```bash
     vllm start --model /path/to/local/model
     ```
5. Choose a small starter model so the upgrade stays practical and fits daily free Copilot execution.
   - Example local model: `qwen3:0.6b`
   - Avoid downloading very large models in this stage.
6. Update Jarvis config if needed to point to the local backend and model:
   - set `LLM_ENGINE = "ollama"` or `LLM_ENGINE = "openjarvis"` in `jarvis/config.py`
   - use `JARVIS_OPENJARVIS_PATH` for the OpenJarvis SDK and `JARVIS_OPENJARVIS_CONFIG` for a custom config file.
7. Start Jarvis and verify it uses local inference only.
   - Run a simple local-query command or start the service.
8. Confirm there is no cloud fallback during startup.
   - Watch logs for `cloud`, `openai`, `anthropic`, `gemini`, or `google`.

Verification:
- A local inference backend is running.
- Jarvis is configured to use `ollama` or `vllm` only.
- No cloud API keys are configured in the current shell or project config.
- The selected model is a small local starter model suitable for lightweight testing.

Notes:
- Keep the setup offline and free by avoiding any paid cloud services.
- Prefer small local models to make this stage solvable with daily free Copilot credits.
- This stage is about enabling local inference first, before installing agents or skills.
