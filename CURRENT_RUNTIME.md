# Current Runtime Baseline — 2026-05-22

**Status:** Active baseline for routing/capability claims.

## Agent Runtime

- Active visible/spawn-allowed agents from `agents_list`: `main`, `intel`, `ops`, `comms`, `sentinel`
- Pentagon roles are now configured as spawnable runtime agents. A smoke test reached the `sentinel` runtime route but hit a transient session-file lock/takeover error before producing content; retry if execution proof is needed.

## Model Posture

- Cloud-native only.
- Main current runtime model: `openai-codex/gpt-5.5` / default `openai/gpt-5.5`.
- Sub-agent protocol model target: `deepseek/deepseek-v4-flash`.
- Compaction model target: `deepseek/deepseek-v4-flash`.
- No active local Ollama / local GPU / local LLM routing.

## Media Providers

- Video configured provider observed on 2026-05-22: Google Veo via `google/*`.
- Other video providers may be listed by tooling but are unavailable until their API keys are configured.

## Memory Status

- Direct file/git memory is active.
- Semantic memory may fail if embedding provider quota is exhausted; use fallback order from `memory/LTM_PROTOCOL.md`.

## Source of Truth Order

1. Live tool output (`agents_list`, provider list tools, git status)
2. `CURRENT_RUNTIME.md`
3. Active protocol files
4. Historical memory/reports only when explicitly needed for audit/history
