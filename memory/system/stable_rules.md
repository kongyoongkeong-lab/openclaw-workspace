# Stable Operational Rules

- Default model routing is hybrid.
- API model handles long-context, tool-heavy, current-knowledge, and final synthesis tasks.
- API model calls must maximize the effective context window according to the selected model spec and current runtime cap.
- `openai-codex/gpt-5.5` is configured as the default 1M-context API runtime entry for fresh sessions.
- Existing sessions may retain a smaller cap until gateway restart and fresh session creation.
- API context budgeting must reserve output and reasoning tokens; do not fill the whole window with input.
- Ollama handles compact private reasoning, local summarization, embeddings, and low-risk worker tasks.
- Treat context overflow as a preventable runtime failure.
- For API mode, compact at 75%, aggressively compact at 90%, and stop expansion at 96% of effective window.
- For local mode, keep conservative context limits and split work into artifacts.
- If API models are unavailable, degrade to local Ollama mode for compact reasoning and local file work.
- Check GPU memory before local LLM or image-generation work.
- Keep local GPU work under 9,728 MiB VRAM unless Jason explicitly approves a monitored exception.
- Use GitHub as the consultation and version-control layer for setup decisions.
- Do not restore old GitHub backup content into the live workspace without review.
- Do not push runtime state, secrets, generated media, caches, or raw memory logs to GitHub.
