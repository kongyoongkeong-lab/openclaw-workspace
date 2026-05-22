# OpenClaw Architecture Decisions

## 2026-05-22: Hybrid Model Runtime Baseline

Decision: Use a hybrid routing policy.

- API model is the default orchestrator for complex, long-context, and tool-heavy work.
- Ollama is the local worker layer for private, compact, and low-risk tasks.
- `qwen3.5:9b` is the primary local reasoning model when VRAM is safe.
- `qwen3.5:4b` and `qwen3.5:2b` are fallbacks for lower-latency or lower-VRAM work.
- `nomic-embed-text:latest` is the local embedding model.
- GitHub is version control for reviewed files, not an automatic backup restore source.
