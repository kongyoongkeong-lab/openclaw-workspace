# OpenClaw Workspace

Production workspace for the OpenClaw Pentagon agent system.

This repository contains operational instructions, workflow guardrails, memory structure, and automation scripts used by the OpenClaw main agent and its supporting agent workspaces.

## Repository Map

- `AGENTS.md` - primary operating instructions for the main OpenClaw agent.
- `.github/copilot-instructions.md` - repository-wide Copilot and agent coding guidance.
- `.github/instructions/` - path-scoped GitHub Copilot instruction files.
- `.github/workflows/` - CI checks for protocol hygiene, markdown, and secret scanning.
- `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md` - structured intake and review gates.
- `memory/` - Git-tracked memory structure and reviewed durable context.
- `docs/` - operational docs and system notes.
- `docs/backup_restore_playbook.md` - Git-backed backup and restore procedure.
- `tools/` - local automation scripts and health checks.
- `shared/` - cross-agent handoff bridge for specs, artifacts, reviews, and decisions.

## Safety Rules

- Do not commit secrets, tokens, browser cookies, API keys, or generated credential files.
- Do not publish private operational data without explicit owner approval.
- Do not write Qdrant, enable production activation, add persistent background tasks, or expand telemetry without explicit approval.
- Treat GitHub as reviewed history, not the source of truth for restoring runtime secrets.

## Local Checks

Run the protocol audit before changing governance, memory, routing, model, or agent instruction files:

```bash
python3 scripts/protocol_audit.py
```

Run markdown lint when editing markdown-heavy areas:

```bash
npx markdownlint-cli2
```
