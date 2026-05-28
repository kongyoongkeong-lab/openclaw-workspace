# D Drive Memory Candidates Review — 2026-05-24

Purpose: review-only extraction from the D: long-term memory scan. Nothing in this file has been promoted to canonical long-term memory yet.

Source index:
- Scan report: `reports/audit/d-drive-long-term-memory-scan-2026-05-24.md`
- Primary archive sampled: `D:/backup/openclaw-system-20260520-124007/config.tar.gz`
- Secondary archive sampled: `D:/backup/openclaw-system-20260520-115144/config.tar.gz`
- Direct duplicate candidates sampled from `D:/Backups_old/**/workspace/MEMORY.md`

Safety policy used:
- No Qdrant/Vault writes.
- No changes to `MEMORY.md`.
- No promotion into `memory/preferences/`, `memory/decisions/`, or `memory/system/`.
- Raw secrets, API keys, OAuth tokens, passwords, and bot tokens are excluded.
- Email/account identifiers from old notes are treated as sensitive metadata and should stay in config/tooling unless Jason explicitly wants them in memory.

## Extraction Summary

- Direct strong candidates in scan: 67.
- Archive strong candidates in scan: 149.
- Most direct candidates were duplicate skill memory templates or OpenClaw/Beszel framework docs, not Jason-specific long-term memory.
- Highest-value recoverable data came from structured memory files inside the 2026-05-20 OpenClaw system backups.
- The current live memory already contains many core facts, but older structured files include useful missing details around shortcuts, routing, memory hygiene, and project rollups.

## Recommended Promotions

### `memory/preferences/jason.md`

Recommended additions or merges:

- Chinese responses are acceptable and often preferred for shortcuts, news, and explanations.
- For complex work, report concrete progress and evidence instead of vague status.
- Prefer reusable scripts under `/home/jason2ykk/.openclaw/workspace/tools/` for recurring tasks.
- Act when the request is clear and reversible.
- Ask before irreversible, destructive, external, security-sensitive, or persistent changes.
- Do not request sudo/elevated access unless genuinely required.
- For Telegram/mobile output, use compact sections and avoid walls of text.
- Jason uses short Chinese commands as workflow triggers.
- New confirmed 4-character Chinese shortcuts should be added to `shortcuts.md` and routed in `AGENTS.md` when automatic execution is needed.
- Daily news style preference: Chinese, mobile-friendly, "茶餐室聊天风 + 工程师清晰度".
- Daily news priority: Malaysia relevance first, then global news with Malaysia/Asia impact.
- Quota/status tools may show account-level quota summaries but must not reveal tokens.

Notes:
- Do not downgrade or overwrite the live poster-generation preferences currently in `memory/preferences/jason.md`; those appear newer and more detailed than the D: backup.

### `memory/decisions/openclaw.md`

Recommended additions or merges:

- `@main` is responsible for intent decomposition, delegation, synthesis, and the final user-facing response.
- Specialized role mapping:
  - `@intel`: research, web search, file parsing, vector retrieval.
  - `@ops`: code, terminal execution, Docker/devops tasks.
  - `@comms`: formatting and communication outputs.
  - `@sentinel`: security, VRAM monitoring, hallucination/safety checks.
- Local qwen should not become the full tool-calling orchestrator until tool-continuation reliability is improved and re-tested.
- Correct model failover rule: if API/quota/provider fails, compress the task packet and hand off to local qwen; if local VRAM exceeds 9.5GB or local tool continuation fails, use API or wait/unload local model.
- Manual model-routing shortcuts are policy/routing shortcuts only, not OpenClaw runtime config changes: `API模型`, `本地模型`, `混合模型`, `当前模型`, `模型策略`.
- High-value skills previously enabled/installed: `openclaw-backup`, `openclaw-security-guard`, `docker`, `testing-patterns`, `e2e-testing-patterns`.
- Running backup jobs, security hardening, token rotation, Docker container actions, or destructive operations still requires explicit approval.
- Avoid enabling write-capable GitHub triage/PR automation until token scopes and write safety are reviewed.
- Archive files under `memory/archive/**` are retrieval-low-priority; prefer curated core files and `memory/projects/*.md` rollups unless historical provenance is explicitly needed.

### `memory/system/stable_rules.md`

Recommended additions or merges:

- `额度切换`: run `/home/jason2ykk/.openclaw/workspace/tools/codex_quota_preflight.py`; query safe quota summaries and update per-agent OpenAI-Codex auth order without exposing tokens/secrets.
- `塔维切换`: run `/home/jason2ykk/.openclaw/workspace/tools/tavily_key_preflight.py --check-all`; report selected Tavily account/status only, never API keys/secrets.
- OpenAI/Codex OAuth profile failover is not guaranteed automatic when an active account quota is exhausted; check quota and switch deliberately.
- Account/profile IDs are dynamic and must be discovered from current auth profiles/config rather than hardcoded as permanent.
- Protocol modes known from backup: `stable`, `self_improvement`, `architect_mode`, `emergency_fix`, `lockdown`.
- Production activation, new agents, telemetry expansion, Qdrant writes, workflow changes, autonomous scheduling, and persistent background tasks require explicit approval.
- Daily news output should be Chinese, concise, mobile-friendly, and put Malaysia impact first.
- Do not fabricate missing news; if source coverage is insufficient, say so.
- `memory/projects/` stores concise project rollups and should be preferred over old dated logs.
- Daily/runtime logs should not pollute root memory.
- `memory/archive/**` is low-priority / explicit-use only: prefer core memory or project rollups unless Jason asks for historical audit/provenance.

### New `memory/projects/*.md` Rollups

The D: backup contains concise project rollups that are likely worth restoring after review:

- `memory/projects/model-routing.md`
- `memory/projects/comfyui-gpu.md`
- `memory/projects/media-workflows.md`
- `memory/projects/openclaw-runtime-pipeline.md`
- `memory/projects/pentagon-memory.md`
- `memory/projects/context-governance.md`

Recommended action:
- Restore these as new files only after Jason approval.
- Treat them as curated rollups, not raw logs.
- Do not import older dated memory logs unless a rollup is missing critical provenance.

High-signal facts from project rollups:

- Model routing:
  - Production default is Hybrid Mode.
  - API/main handles orchestration, tool-heavy workflows, long context, web/search, quota/account tasks, final synthesis, and security-sensitive tasks.
  - Local `ollama/qwen3.5:9b` handles compact/private/direct reasoning and GPU-worker tasks only when VRAM is safe.
  - Local worker execution remains gated; actual local spawning requires explicit approval.

- ComfyUI/GPU:
  - GPU baseline is RTX 4070 Super class, 12GB VRAM.
  - SDXL Base 1.0 workflow was prepared for OpenClaw -> ComfyUI API -> SDXL GPU -> automated output.
  - Expected SDXL inference time was noted around 2-4 minutes for 28-step jobs.
  - Validation criteria: PNG output appears, no OOM/crash/traceback, GPU returns to idle.

- Media workflows:
  - JPEG may be preferable to PNG for delivery-constrained media artifacts.
  - Practical mobile poster configuration: 512x1024 output with PIL optimization and JPEG quality around 85.
  - Avery Care Centre document processing was a one-off document/PDF analysis event; keep as provenance only unless Jason asks.

- Runtime pipeline:
  - Early runtime design used parallel execution concepts, including `asyncio.gather()` in RuntimeKernel experiments.
  - Pentagon routing pattern: research/search to `@intel`, execution/system to `@ops`, final safety/validation via `@sentinel`, final formatting via `@comms`.
  - Hardware baseline: RTX 4070 Super class GPU, WSL2, Ollama, Qwen 3.5 9B local-first/private worker where safe.

- Pentagon memory:
  - Root `MEMORY.md` is the curated high-signal memory index.
  - `memory/preferences/jason.md`, `memory/decisions/openclaw.md`, and `memory/system/stable_rules.md` are canonical structured memory targets.
  - Large noisy dated logs should be summarized into project rollups before archival.

- Context governance:
  - Track drift velocity and causal pressure signals, not only instantaneous metric values.
  - Governance should stay bounded; avoid expanding metrics/agents/telemetry unless explicit thresholds or user approval justify it.

## Do Not Promote Without Separate Approval

- Raw dated logs from old backups.
- `memory/.dreams/**`, `episodic.jsonl`, `compression.jsonl`, and telemetry/event files.
- Skill-local `self-improving-*/memory.md` files, which appear to be duplicated templates.
- OpenClaw/Beszel framework docs under `D:/Backups_old/Beszel/**`; useful as reference, not Jason-specific memory.
- Account emails or profile IDs as permanent memory. Use current config/profile discovery instead.
- Any content from the damaged 13GB archive until the archive is repaired or independently verified.

## Scan Limitations To Preserve

- `D:/backup/pentagon_backup_2026-04-25_0437.tar.gz` appears damaged/truncated and returned `Unexpected EOF`; no long-term memory hit was seen before failure.
- 12 `.7z`/`.rar` archives were not inspected because `7z`, `7zz`, and `unrar` were unavailable.
- Two old backup directories had permission-denied errors during the original scan.

## Proposed Next Step

If approved, promote in two small patches:

1. Patch live structured memory:
   - `memory/preferences/jason.md`
   - `memory/decisions/openclaw.md`
   - `memory/system/stable_rules.md`

2. Restore project rollup files:
   - create `memory/projects/`
   - add the six reviewed rollup files listed above

No Qdrant/Vault write should happen unless Jason explicitly asks for it.
