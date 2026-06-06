# Stage 3 — Setup Local Agent Presets

Goal: Initialize Jarvis presets that are designed to work offline and with local inference.

Tasks:
1. Review available starter presets from `openjarvis/OpenJarvis/README.md`.
2. Pick a local-first preset, such as:
   - `chat-simple` (recommended local-only)
   - `morning-digest-minimal` (cloud-dependent by default; requires Gmail/remote TTS)
3. Initialize Jarvis with the chosen preset:
   ```bash
   uv run jarvis init --preset chat-simple
   ```
   If `uv` is unavailable, set `JARVIS_OPENJARVIS_CONFIG=openjarvis/OpenJarvis/configs/openjarvis/examples/chat-simple.toml` and start Jarvis normally.

4. Verify the preset config uses a local backend and model.
5. Adjust the preset if needed to remove any cloud-only features such as remote TTS or cloud connectors.

Verification:
- Jarvis starts successfully with the selected preset.
- The preset does not require OAuth cloud connectors or paid API keys.
- The agent uses local inference for responses.

Notes:
- Prefer presets that are described as "minimal" or local-friendly.
- If the preset still references cloud features, disable them explicitly.
