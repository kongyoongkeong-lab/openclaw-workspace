# Memory Contract

## Source Of Truth

- Root `MEMORY.md`: curated stable long-term memory.
- `memory/`: structured durable memory.
- `.github/copilot-instructions.md`: repository-wide GitHub Copilot rules.
- `.github/instructions/*.instructions.md`: path-specific GitHub Copilot rules.

## Directory Routing

| Memory Type | Path |
|---|---|
| Curated summary | `MEMORY.md` |
| Daily logs | `memory/logs/YYYY-MM-DD.md` |
| Legacy daily logs | `memory/YYYY-MM-DD.md` |
| User preferences | `memory/preferences/` |
| Architecture/workflow decisions | `memory/decisions/` |
| System rules and capability registry | `memory/system/` |
| Project context | `memory/projects/<project>/` |
| Chat/group context | `memory/groups/<surface>/` |
| Failure memory | `memory/errors/` |
| Candidate memories | `memory/review/` |

## Promotion Policy

1. Capture transient observations in logs or review files.
2. Verify candidate facts against workspace files, runtime status, or user
   confirmation.
3. Promote stable facts into `MEMORY.md` or the most specific structured file.
4. Remove or mark stale candidates after promotion.

## GitHub Alignment

GitHub's Copilot repository instruction model supports:

- `.github/copilot-instructions.md` for repository-wide instructions.
- `.github/instructions/NAME.instructions.md` with `applyTo` frontmatter for
  path-specific instructions.
- `AGENTS.md` for coding-agent behavior.

This workspace uses all three without making GitHub an automatic restore source.

## Safety Rules

- No secrets, tokens, browser cookies, OAuth files, raw credentials, raw traces,
  JSONL streams, or generated auth material in memory.
- No Qdrant writes, auto-memory learning, global compaction, or retrieval
  expansion without explicit Jason approval.
- Do not migrate legacy memory files during unrelated tasks.
