# OpenClaw Project Memory

## Purpose

Build Jason's personal AI operating system: a local-first orchestration layer
that understands short commands, coordinates the Pentagon agent roles, invokes
tools, automates workflows, and reports verifiable status through Telegram and
local workspace artifacts.

## Runtime Contract

- `@main` is the Pentagon orchestrator.
- `@intel` researches and writes citation-backed findings to `shared/specs/`.
- `@ops` executes shell, Python, Docker, CDP, and automation tasks and writes
  outputs to `shared/artifacts/`.
- `@comms` formats reports and channel-ready deliverables.
- `@sentinel` handles security, VRAM guardrails, hallucination checks, and
  cross-review.

## Memory Contract

- `MEMORY.md` is the curated long-term summary.
- `memory/` stores structured durable context.
- `.github/copilot-instructions.md` and `.github/instructions/*.instructions.md`
  guide GitHub Copilot and GitHub-side review behavior.
- Qdrant is retrieval support only unless Jason explicitly approves writes.

## Current Memory Implementation

- File-first durable memory is active.
- `tools/memory_extract.py` provides semi-automatic candidate extraction into
  review files.
- Mem0/Zep/LlamaIndex are not active integrations.
- Existing legacy daily logs remain at `memory/YYYY-MM-DD.md`; new daily logs
  should use `memory/logs/`.
