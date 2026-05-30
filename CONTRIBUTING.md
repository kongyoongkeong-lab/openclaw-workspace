# Contributing

This workspace is operational infrastructure. Keep changes small, reviewable, and scoped to the requested behavior.

## Before Editing

- Read `AGENTS.md` and `.github/copilot-instructions.md` for current guardrails.
- Check whether the target area has a path-specific file under `.github/instructions/`.
- Avoid broad cleanup, generated-file churn, and unrelated formatting changes.

## Change Rules

- Do not use `git add .`.
- Do not commit secrets or machine-local runtime state.
- Do not revert changes you did not make unless explicitly requested.
- Do not enable production activation, persistent background tasks, telemetry expansion, Qdrant writes, or new agents without explicit approval.

## Validation

For governance, memory, routing, model, or agent instruction changes, run:

```bash
python3 scripts/protocol_audit.py
```

For markdown changes, run markdown lint when available:

```bash
npx markdownlint-cli2
```
