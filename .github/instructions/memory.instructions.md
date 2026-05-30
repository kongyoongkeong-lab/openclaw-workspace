---
applyTo: "MEMORY.md,memory/**/*.md,**/MEMORY.md"
---

# Memory Structure Instructions

Follow the repository memory contract when editing durable memory files.

- Keep root `MEMORY.md` curated and stable. Do not add raw chat logs,
  transient runtime output, generated media paths, secrets, tokens, cookies,
  or unverified claims.
- Store daily/runtime notes in `memory/logs/YYYY-MM-DD.md`. Existing
  root-level `memory/YYYY-MM-DD.md` files are legacy logs and may be read, but
  new logs should use `memory/logs/`.
- Store project memory in `memory/projects/<project>/`, group or channel
  memory in `memory/groups/<surface>/`, durable user preferences in
  `memory/preferences/`, architecture decisions in `memory/decisions/`, stable
  runtime rules in `memory/system/`, failure patterns in `memory/errors/`, and
  unapproved candidates in `memory/review/`.
- Before promoting a fact from `memory/review/` into curated memory, verify it
  against workspace files or current runtime evidence.
- Qdrant writes, auto-memory learning, compaction, and global retrieval changes
  require explicit Jason approval unless a specific approved workflow grants
  that write.
- GitHub is a reviewed history and Copilot guidance layer. Do not treat GitHub
  as an automatic restore source for live memory.
