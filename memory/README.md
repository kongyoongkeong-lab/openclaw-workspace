# OpenClaw Memory Structure

This directory is the durable memory layer for Jason's OpenClaw workspace.
Root `MEMORY.md` remains the high-signal curated summary; this directory holds
structured supporting memory.

## Layout

| Path | Purpose |
|---|---|
| `logs/` | Daily/runtime logs. New logs use `YYYY-MM-DD.md`. |
| `projects/` | Project-specific context, decisions, and status. |
| `groups/` | Conversation memory by chat surface or group. |
| `preferences/` | Durable Jason preferences and workflow defaults. |
| `decisions/` | Architecture and workflow decisions. |
| `system/` | Stable operational rules and capability registry. |
| `errors/` | Failure patterns, recovery steps, prevention rules. |
| `review/` | Candidate memories waiting for human or evidence review. |

## Promotion Rules

- Keep stable facts in `MEMORY.md`, `preferences/`, `decisions/`, and
  `system/`.
- Keep raw or semi-raw observations in `logs/` or `review/`.
- Never store secrets, tokens, browser cookies, raw traces, JSONL streams, or
  generated auth material.
- Promote repeated failures to `errors/` only after sanitizing sensitive
  details.
- Do not write to Qdrant or enable automatic memory learning without explicit
  approval.

## Legacy Files

Existing files named `memory/YYYY-MM-DD.md` are legacy daily logs. They remain
readable for retrieval continuity. New daily logs should be placed under
`memory/logs/`.
