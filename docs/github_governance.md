# GitHub-Governed Setup Policy

Status: active baseline
Owner: Jason / Pentagon `@main`
Date: 2026-05-22

## Purpose

GitHub is the consultation and version-control layer for the optimized OpenClaw setup.

This workspace must not blindly follow the old backup currently present in the GitHub account. GitHub should be used to:

- Keep reviewed setup decisions visible.
- Track small, auditable commits.
- Preserve rollback points.
- Support future issue/PR review workflows.
- Provide Copilot with a constrained review and implementation contract through
  `.github/copilot-instructions.md`.

GitHub should not be used to:

- Restore raw runtime dumps into the live workspace.
- Store secrets, tokens, OAuth files, raw memory logs, or bulky generated artifacts.
- Override local validated configuration without review.
- Replace the local hybrid API/Ollama model policy with remote backup defaults.

## Current Remote

```text
repo: kongyoongkeong-lab/openclaw-workspace
url: https://github.com/kongyoongkeong-lab/openclaw-workspace
branch: main
visibility: public
```

## Required Workflow

For setup changes:

1. Inspect local status.
2. Inspect GitHub remote metadata with `gh`.
3. Update local files first.
4. Run validation and secret checks.
5. Commit small, reviewable changes.
6. Push only after Jason explicitly approves public GitHub publication.

## Remote Backup Handling

Old GitHub branches and backups are reference material only. Do not restore,
merge, or checkout a backup branch into the live workspace as a repair method.

Allowed process:

1. Locate the specific candidate file or snippet with `git ls-tree`, `git show`,
   or `gh` read-only inspection.
2. Read only the function or workflow section needed for the current task.
3. Rewrite the behavior for the current local hybrid runtime, current safety
   invariants, and current file paths.
4. Apply the rewritten local patch to the smallest practical file set.
5. Run `python3 scripts/protocol_audit.py`, syntax checks, and
   `git diff --check`.

Disallowed process:

- `git merge` from old backup branches.
- Branch-wide restore into the workspace.
- Copying stale cloud-only, old VRAM, old agent-activation, or token-bearing
  policy into current runtime files.
- Treating remote backup content as more authoritative than local
  `AGENTS.md`, `MEMORY.md`, `PROTOCOL_INVARIANTS.md`, and
  `config/model_runtime.json`.

## Review Gates

Before pushing:

- `git diff --check` must pass.
- `python3 scripts/protocol_audit.py` must pass without blocking failures.
- Staged secret scan must pass.
- Runtime/token/config files must remain ignored.
- Generated media and raw memory logs must remain out of git.
- Public repo risk must be called out explicitly.

## Copilot Role

GitHub Copilot may help by reviewing PRs, suggesting scoped patches, improving
tests, and keeping documentation consistent. It must not be treated as the live
runtime authority.

Copilot guidance must preserve these boundaries:

- Local workspace files remain the runtime source of truth.
- Hybrid mode remains the model baseline unless Jason explicitly changes it.
- API/Codex handles orchestration and long-context work.
- Ollama handles compact/private worker tasks only after GPU preflight passes.
- Qdrant writes, new agents, telemetry expansion, workflow changes, production
  activation, and persistent background tasks require explicit approval.
- Public pushes and PR updates require exact-file staging and secret checks.

## Current Baseline Commits

```text
f6882c5 Add hybrid model runtime baseline
659adba Add context-resilient hybrid routing
```
