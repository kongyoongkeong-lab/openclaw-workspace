# Pentagon Vault — System Baseline
**Initiated:** 2026-05-08 22:26 GMT+8
**Refreshed:** 2026-05-22 00:20 GMT+8
**Mode:** Cloud-Native (no GPU, no local inference)

## Immutable Facts
- **Runtime:** Pure cloud-native (DeepSeek, no local LLM)
- **Base Path:** `/home/jason2ykk/.openclaw/workspace/`
- **Stack Path:** `~/openclaw-stack/`
- **Config Path:** `~/openclaw-stack/openclaw-config/`
- **GitHub Account:** `kongyoongkeong-lab`

## Active Repositories
| Repo | Purpose | Branch |
|------|---------|--------|
| `openclaw-workspace` | Agent configs + memory + CI | master / develop |
| `openclaw-config` | Gateway + infrastructure configs | master |

## Agent Registry
- @main (Orchestrator): Cloud LLM
- @intel (Research): Cloud LLM + Tavily + Qdrant + GitHub Search
- @ops (Execution): Cloud LLM + Docker + gh CLI
- @comms (Communication): Cloud LLM + Telegram
- @sentinel (Guardian): Cloud LLM + git secret scan

## Running Services
| Service | Port | Type |
|---------|------|------|
| Qdrant | 6333 | Vector memory store (Docker) |
| Redis | 6379 | Cache / queue (Docker) |
| ComfyUI | 8188 | Image generation (CPU mode) |
| Gateway | 8080 | OpenClaw orchestration |

## Token Budgets
- @intel: 2000 tokens
- @ops: 3000 tokens
- @comms: 1500 tokens
- @sentinel: 1000 tokens

## Cache Ratios (Target: 70-90%)
- LTM Cache: 82%
- Vector Cache: 65%
- Context Cache: 78%

## GitHub Credentials
- **PAT Scopes:** `repo`, `workflow`, `read:org`
- **Stored:** `~/.config/gh/hosts.yml` (not in git)
- **Auto-backup:** Daily via cron, tagged `backup-YYYY-MM-DD`
