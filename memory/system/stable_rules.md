# Stable Operational Rules

- Default model routing is hybrid.
- API model handles long-context, tool-heavy, current-knowledge, and final synthesis tasks.
- Ollama handles compact private reasoning, local summarization, embeddings, and low-risk worker tasks.
- Check GPU memory before local LLM or image-generation work.
- Keep local GPU work under 9,728 MiB VRAM unless Jason explicitly approves a monitored exception.
- Do not restore old GitHub backup content into the live workspace without review.
- Do not push runtime state, secrets, generated media, caches, or raw memory logs to GitHub.
