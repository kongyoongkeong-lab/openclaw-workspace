# OpenClaw Architecture Decisions

## 2026-05-22: Hybrid Model Runtime Baseline

Decision: Use a hybrid routing policy.

- API model is the default orchestrator for complex, long-context, and tool-heavy work.
- Ollama is the local worker layer for private, compact, and low-risk tasks.
- `qwen3.5:9b` is the primary local reasoning model when VRAM is safe.
- `qwen3.5:4b` and `qwen3.5:2b` are fallbacks for lower-latency or lower-VRAM work.
- `nomic-embed-text:latest` is the local embedding model.
- GitHub is version control for reviewed files, not an automatic backup restore source.

## 2026-05-22: Context-Resilient Runtime Upgrade

Decision: Make context pressure and provider failure first-class routing concerns.

- Live context is capped by policy and should be compressed/offloaded before it becomes a blocker.
- Long outputs and durable decisions must be stored as files, then referenced by path.
- API unavailability triggers a local Ollama fallback path.
- Local fallback is scoped to compact reasoning, local file work, summarization, routing, and embeddings.
- Internet-current or high-complexity claims still require API/search recovery or explicit degraded-mode reporting.
