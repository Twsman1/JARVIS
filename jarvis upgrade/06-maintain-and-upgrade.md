# Stage 6 — Maintain and Upgrade Offline Jarvis

Goal: Provide a simple maintenance path for the free, offline Jarvis setup.

Tasks:
1. Document how to update local models safely.
   - Pull newer Ollama models locally.
   - Refresh vLLM model files.
2. Explain how to keep Jarvis local:
   - avoid enabling `cloud` engine
   - keep cloud API keys unset
3. Add a note on how to check system health and engine status:
   - `jarvis doctor`
   - local backend service status
4. Encourage periodic review of the config files:
   - `openjarvis/OpenJarvis/configs/openjarvis/config.toml`
   - preset files under `openjarvis/OpenJarvis/configs/openjarvis/examples/`

Verification:
- A maintenance checklist exists for local-only upgrades.
- No cloud service restart or API key setup is part of maintenance.
- The project remains free and offline by design.

Notes:
- Keep this file as the long-term guide for staying off-cloud.
- Focus on local resources and offline model refresh workflows.
