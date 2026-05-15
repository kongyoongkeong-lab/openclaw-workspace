# Git Upgrade Protocol v1

**Mode:** Documentation only  
**Runtime impact:** None  
**Activation:** Manual review only; no workflow activation

This protocol governs safe preparation of git-based upgrades and pull requests.

## Non-Goals

This protocol does not:

- activate workflows
- deploy runtime changes
- add telemetry
- add agents
- enable global automation

## Upgrade Preparation Flow

### 1. Inspect Workspace

Always start with:

```bash
git status --short
```

Review all dirty files before staging anything.

### 2. Use Exact-File Staging Only

Never use:

```bash
git add .
```

Stage only the files required for the upgrade:

```bash
git add exact/path/file-1 exact/path/file-2
```

### 3. Exclude Forbidden Files

Never stage:

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

### 4. Workflow Scope Gate

Workflow files require separate approval:

- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`

If workflow scope is missing, exclude workflow files from the PR.

### 5. Dirty Workspace Rule

If unrelated dirty files exist, use a clean worktree for the upgrade.

Required behavior:

1. Preserve unrelated dirty files unstaged.
2. Apply the upgrade in a clean worktree when practical.
3. Stage only exact intended files.
4. Do not mix opportunistic cleanup with upgrade commits.

### 6. Verify Staged Files

Before commit:

```bash
git diff --cached --name-only
```

The staged list must be minimal and intentional.

### 7. Pre-PR Confirmation

Before opening or updating a PR, confirm:

- changed files are minimal
- changed files are intentional
- forbidden files are excluded
- workflow files have separate approval or are excluded
- dirty workspace changes are not accidentally included

## Manual PR Checklist

- [ ] Ran `git status --short`
- [ ] Did not use `git add .`
- [ ] Used exact-file staging only
- [ ] Ran `git diff --cached --name-only`
- [ ] Excluded forbidden files and directories
- [ ] Excluded workflow files unless separately approved
- [ ] Confirmed minimal intentional PR scope

## Locked Safety Statement

Git write operations must be narrow, auditable, and explicitly scoped. Broad staging is prohibited.
