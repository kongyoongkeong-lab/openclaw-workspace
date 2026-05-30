# Backup And Restore Playbook

This playbook defines the safe path for Git-backed OpenClaw workspace recovery.
It treats GitHub as reviewed history, not as an automatic source of truth for
runtime secrets or local state.

## Backup Layers

| Layer | Purpose | Recommended Mechanism |
| --- | --- | --- |
| Git commits | Reviewed memory structure, governance docs, and safe scripts | Small commits with exact staging |
| GitHub remote | Off-machine copy of reviewed commits | Push only after local verification |
| Local sensitive backup | Runtime configs, tokens, logs, and browser/session state | Encrypted local backup after explicit approval |
| External services | GitHub security settings, CodeQL, branch protection | Record settings in docs and verify through `gh api` |

## Routine Backup

1. Check status with `git status --short`.
2. Review each changed file before staging.
3. Stage exact files only. Do not use `git add .`.
4. Run relevant checks:
   - `python3 scripts/protocol_audit.py`
   - `pnpm dlx markdownlint-cli2 README.md SECURITY.md CONTRIBUTING.md .github/**/*.md memory/**/*.md docs/**/*.md`
5. Commit with a focused message.
6. Push to `origin/main` only when branch protection and security policy allow it.

## Restore Rules

Use restore in the smallest possible scope.

- Prefer `git show <commit>:<path>` for inspection before restoring.
- Prefer file-level restore over branch-wide restore.
- Do not run destructive commands such as `git reset --hard` unless Jason explicitly requests that exact operation.
- Do not restore secrets, browser cookies, chat exports, or runtime tokens from GitHub.
- Re-run protocol audit after restoring governance, memory, model-routing, or automation files.

## Emergency Recovery

1. Freeze new changes and record `git status --short`.
2. Identify the last known-good commit with `git log --oneline`.
3. Inspect candidate files with `git show`.
4. Restore only the required files.
5. Run protocol audit and markdown lint.
6. Commit the recovery with a message that names the incident and restored scope.

## Sensitive Backup Gate

Full system backups can include tokens, local config, browser state, chat logs,
and private runtime data. They require explicit Jason approval before execution.
When approved, create encrypted local/off-machine backup artifacts and record
only non-secret metadata in Git.
