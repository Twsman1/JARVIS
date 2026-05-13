# Stage 5 — Validate Offline No-Cloud Operation

Goal: Confirm the Jarvis upgrade is fully offline and free of cloud dependencies.

Tasks:
1. Run a simple Jarvis query or preset action.
   - Example:
     ```bash
     uv run jarvis ask "Hello, Jarvis. Tell me a short summary of the local setup."
     ```
2. Check the active engine and model in logs or runtime output.
3. Ensure no cloud engine selection occurs during startup:
   - no `cloud` backend
   - no cloud model prefixes (`gpt-`, `claude-`, `gemini-`, `openrouter/`, `chatgpt-`)
4. Verify environment variables do not include cloud API keys.
5. If any cloud dependency appears, revert to local model and backend settings.

Verification:
- Jarvis responds using local inference.
- No cloud API keys are required or referenced.
- The system remains usable without internet access for inference.

Notes:
- This stage is critical for confirming the transition to an offline workflow.
- Keep all tests short and bounded to fit daily free Copilot sessions.
