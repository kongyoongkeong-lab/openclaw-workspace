# GitHub-Governed Setup Policy

Status: active baseline
Owner: Jason / Pentagon `@main`
Date: 2026-05-31

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

## GitHub Governance Status

As of 2026-05-31, GitHub-side governance is split into active protections and
ready-but-blocked follow-ups.

Active:

- Repository description:
  `OpenClaw workspace memory, automation, and GitHub governance baseline`
- Repository topics:
  `openclaw`, `ai-agent`, `memory-system`, `automation`, `telegram-bot`,
  `copilot-instructions`, `github-governance`
- Delete branch on merge is enabled.
- Secret scanning, push protection, Dependabot vulnerability alerts, and
  Dependabot security updates are enabled.
- CodeQL default setup is active for Python.
- `main` branch protection requires:
  - PR review count: `1`
  - CODEOWNERS review
  - stale review dismissal
  - conversation resolution
  - linear history
  - no force pushes
  - no branch deletion
  - required status check: `Analyze (python)`
- Standard labels exist for priority, type, area, and workflow status:
  `priority:p0`, `priority:p1`, `priority:p2`, `type:bug`, `type:task`,
  `type:security`, `area:memory`, `area:automation`, `area:github`,
  `area:backup`, `status:blocked`, and `status:needs-review`.
- `CODE_OF_CONDUCT.md` defines review and collaboration boundaries for public
  GitHub interactions.
- `LICENSE.md` documents the current all-rights-reserved posture. This
  repository is public for governance and review visibility, not open-source
  redistribution.

Ready but not active:

- Repository ruleset `main-governance-ready` exists in `disabled` mode. It
  mirrors the active branch protection rule but is not enforced. GitHub Free
  does not support `evaluate` mode for this repository, and enabling an active
  ruleset should be a separate decision because rulesets can remove the current
  admin bypass behavior.

Blocked:

- `.github/workflows/*.yml` files are local-only until the GitHub token has the
  `workflow` scope. GitHub rejects workflow pushes without that scope.
- Formal `.github/dependabot.yml` scheduling remains postponed until the remote
  has tracked dependency manifests or tracked GitHub Actions workflows for
  Dependabot to update.

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
6d2e698 Add GitHub-aligned memory structure
20c9ca4 Add GitHub repository governance
ec648d4 Remove unusable Dependabot schedule
2f37cba Add GitHub review and restore gates
8feb0e6 Document GitHub governance follow-ups
```
