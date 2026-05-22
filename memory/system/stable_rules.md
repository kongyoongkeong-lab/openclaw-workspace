# Stable Operational Rules

- Default model routing is hybrid.
- API model handles long-context, tool-heavy, current-knowledge, and final synthesis tasks.
- Ollama handles compact private reasoning, local summarization, embeddings, and low-risk worker tasks.
- Treat context overflow as a preventable runtime failure.
- At 50% estimated context pressure, summarize and offload into `docs/` or structured `memory/`.
- At 80% estimated context pressure, stop expanding live context, write a handoff summary, and resume from files.
- If API models are unavailable, degrade to local Ollama mode for compact reasoning and local file work.
- Check GPU memory before local LLM or image-generation work.
- Keep local GPU work under 9,728 MiB VRAM unless Jason explicitly approves a monitored exception.
- Do not restore old GitHub backup content into the live workspace without review.
- Do not push runtime state, secrets, generated media, caches, or raw memory logs to GitHub.
