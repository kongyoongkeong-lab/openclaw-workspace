# GitHub Copilot Instructions

Guide GitHub Copilot so suggestions, reviews, tests, and PRs preserve Jason's
OpenClaw/Pentagon runtime contract.

## Runtime Source Of Truth

- Local workspace files are the source of truth for runtime behavior.
- GitHub is a reviewed history, consultation, CI, and PR review layer.
- Do not restore old backup content or remote protocol files into the live
  workspace without explicit review.
- Treat the active model policy as hybrid: API/Codex handles orchestration,
  long-context work, tool-heavy work, and final synthesis.
- Ollama handles compact/private worker tasks only after GPU preflight passes.
- Do not replace hybrid mode with cloud-native-only, API-only, or local-only
  policy unless Jason explicitly requests that change.

## Safety Invariants

- Do not add new agents unless explicitly requested.
- Do not activate production behavior unless explicitly requested.
- Do not add telemetry unless explicitly requested.
- Do not add persistent background tasks unless explicitly requested.
- Do not modify workflow files unless explicitly requested.
- Do not write to Qdrant unless explicit approval or a specific approved
  workflow grants that write.
- Do not print, commit, or store secrets, tokens, OAuth files, raw credential
  files, browser cookies, or generated auth material.
- Keep OpenClaw runtime config changes separate from docs and audit changes.

## Model And GPU Policy

- Preserve the RTX 4070 SUPER hardware baseline.
- Preserve the 9,728 MiB used-VRAM hard ceiling for local inference.
- Require `tools/check_gpu.sh` before local LLM, local vision, or image
  generation work.
- Prefer `qwen3.5:9b` for primary local reasoning, `qwen3.5:4b` for faster or
  lower-headroom work, and `qwen3.5:2b` for tiny routing/classification.
- Do not claim a local model is usable unless it is listed in
  `config/model_runtime.json` and verified by local status checks.

## Agent Coordination

- Treat Pentagon agents as configured logical roles unless current runtime
  evidence proves they are active or spawnable.
- Use `agent_registry.json` as the routing registry before proposing
  inter-agent dispatch.
- Do not use stale `sessions_send(agent=...)` syntax.
- Prefer explicit `agentId`, verified `label`, or verified `sessionKey`
  routing shapes when documenting OpenClaw session dispatch.

## Retrieval And Memory

- Qdrant may be read for retrieval when the workflow allows it.
- Qdrant writes, upserts, compaction, and global auto-RAG require explicit
  approval.
- Redis cache is optional support only and must not cache secrets, raw logs,
  traces, JSONL streams, browser profiles, or cookies.
- Do not add auto-memory learning without explicit approval.

Forbidden retrieval/cache paths and content include:

- `.env`
- tokens or token-containing files
- `logs/`
- `traces/`
- `storage/`
- `qdrant/`
- `redis/`
- `models/`
- `*.jsonl`
- `__pycache__/`
- `*.pyc`
- `node_modules/`
- browser profiles
- cookies

## Git Safety

- Never suggest `git add .`.
- Use exact-file staging only, for example:

```bash
git add exact/path/file-a exact/path/file-b
```

- Never stage secrets, runtime memory logs, generated cache files, raw model
  registries, browser profiles, cookies, bulky media, or local backups.
- Public GitHub publication requires explicit approval from Jason.
- Keep PRs minimal and avoid opportunistic cleanup.
- Confirm the changed file list before suggesting commit or PR actions.

## Testing And Audit Expectations

- Run `python3 scripts/protocol_audit.py` after protocol, model-routing,
  GitHub-governance, or Copilot-instruction edits.
- Run `git diff --check` before suggesting commit or PR actions.
- Add or update deterministic tests when touching routing, context budgeting,
  retrieval, render behavior, or safety enforcement.
- Prefer local validation before asking Copilot to open or update a PR.
