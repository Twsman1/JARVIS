# Stage 4 — Install Free Offline Skills and Tools

Goal: Add useful skills and tools that work without cloud APIs or paid services.

Tasks:
1. Identify skills and tools that are offline-friendly.
   - Use local catalog skills if available.
   - Avoid any connector requiring cloud API keys.
2. Install a basic skill set using Jarvis CLI:
   ```bash
   jarvis skill install hermes:arxiv
   jarvis skill sync hermes --category research
   ```
3. Confirm the installed skills do not depend on cloud backends.
4. If tools are enabled, verify they access local resources only.
5. Keep the installed skill set small enough for daily free Copilot execution.

Verification:
- Skills install without requiring cloud API keys.
- No skill downloads or tool setups depend on paid APIs.
- Jarvis can invoke at least one local skill successfully.

Notes:
- This stage focuses on expanding Jarvis capability while remaining offline.
- Avoid skills that inherently require cloud APIs, like web scraping services or remote search connectors.
