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

## 2026-05-22: API Context Maximization and GitHub Governance

Decision: API model calls should maximize the effective context budget, while GitHub acts as the setup consultation and version-control trail.

- Official OpenAI model specs define the upper context window.
- OpenClaw runtime/session status defines the practical cap when it is smaller than the official model window.
- Effective context budget is the lower of the model spec window and observed runtime cap.
- Output and reasoning tokens must be reserved inside the context window.
- GitHub-backed setup changes should be committed as small reviewable units and not copied from old backups blindly.

## 2026-05-22: 1M Context Patch Applied

Decision: Configure `openai-codex/gpt-5.5` as the default 1M-context runtime entry for new OpenClaw sessions.

- Persistent OpenClaw config now advertises `openai-codex/gpt-5.5` with a 1,000,000-token context window.
- `openclaw models list` shows the configured default as approximately 977K visible context.
- Existing sessions retain their prior 272K cap until gateway restart and fresh session creation.
- Budget tooling must distinguish configured runtime budget from current-session budget.
