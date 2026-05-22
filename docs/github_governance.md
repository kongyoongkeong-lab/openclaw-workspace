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

GitHub should not be used to:

- Restore raw runtime dumps into the live workspace.
- Store secrets, tokens, OAuth files, raw memory logs, or bulky generated artifacts.
- Override local validated configuration without review.

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

## Review Gates

Before pushing:

- `git diff --check` must pass.
- Staged secret scan must pass.
- Runtime/token/config files must remain ignored.
- Generated media and raw memory logs must remain out of git.
- Public repo risk must be called out explicitly.

## Current Baseline Commits

```text
f6882c5 Add hybrid model runtime baseline
659adba Add context-resilient hybrid routing
```
