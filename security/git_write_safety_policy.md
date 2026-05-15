# Git Write Safety Policy v1

**Mode:** Documentation only  
**Runtime impact:** None  
**Scope:** Safe git staging, commits, and PR preparation

## Core Rule

Never use broad staging commands.

```bash
# Forbidden
git add .
```

Use exact-file staging only.

```bash
# Required pattern
git add path/to/file-a.md path/to/file-b.py
```

## Required Pre-Staging Check

Always inspect the working tree before staging:

```bash
git status --short
```

Only stage files that are explicitly intended for the current change.

## Forbidden Staging Targets

Never stage any of the following:

- `.env`
- tokens or token-containing files
- `logs/`
- `traces/`
- `storage/`
- `qdrant/`
- `redis/`
- `models/`
- `*.jsonl`
- `__pycache__/`
- `*.pyc`
- `node_modules/`
- browser profiles
- cookies

If any forbidden file appears in `git status --short`, leave it unstaged and investigate separately.

## Workflow File Approval Gate

Workflow files require separate explicit approval before staging:

- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`

If workflow scope is not explicitly approved, exclude workflow files from the PR.

## Dirty Workspace Handling

For dirty workspace changes:

1. Do not stage opportunistically.
2. Use a clean worktree for the intended change.
3. Carry over only exact files required for the PR.
4. Re-run `git status --short` before staging.

## Required Pre-Commit Check

Before every commit, verify the staged set:

```bash
git diff --cached --name-only
```

Confirm every staged file is minimal, intentional, and within scope.

## Required Pre-PR Check

Before every PR:

1. Confirm changed files are minimal and intentional.
2. Confirm no forbidden paths are staged or included.
3. Confirm workflow files are excluded unless separately approved.
4. Confirm no unrelated dirty workspace changes are included.

## Summary

Safe git write flow:

```bash
git status --short
git add exact/file.md another/exact/file.py
git diff --cached --name-only
# commit only after confirming minimal intentional changes
```
