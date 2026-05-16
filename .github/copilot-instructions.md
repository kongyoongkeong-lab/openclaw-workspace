# GitHub Copilot Instructions v1

These instructions guide GitHub Copilot when helping with OpenClaw code, tests, documentation, and pull requests.

## Project Context

- OpenClaw Stable Baseline v1 exists.
- Git Write Safety Policy v1 exists.
- Context Manager v1 is live.
- Qdrant is read-only.
- Redis retrieval cache is validated.
- Global RAG auto-enable is blocked.
- Manual RAG command is removed/not present.
- Interface Verification v1 passed.

## Core Safety Rules

1. Never suggest:

```bash
git add .
```

2. Always use exact-file staging:

```bash
git add exact/path/file-a exact/path/file-b
```

3. Do not modify runtime behavior unless explicitly requested.

4. Do not add any of the following without explicit approval:
   - agents
   - telemetry
   - governance layers
   - workflow files
   - deployment behavior
   - runtime control paths

5. Preserve the locked render policy. The `progress` command must return exactly:

```text
Stable. No user action required.
```

6. Preserve Context Manager v1 live guard.

7. Preserve Qdrant read-only policy.

8. Preserve Redis retrieval cache safety.

9. Never suggest committing or staging:
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

10. Treat `.github/workflows/*` as special approval files. Do not create, edit, stage, or include workflow files unless workflow scope is explicitly approved.

11. Prefer tests before implementation.

12. Prefer small PRs with minimal file diffs.

## Development Guidance

### Before Implementation

- Identify the smallest safe change.
- Prefer adding or updating tests first.
- Confirm whether the request is documentation-only, validation-only, or runtime-changing.
- If runtime-changing, require explicit user intent.

### During Implementation

- Keep changes scoped to requested files.
- Avoid opportunistic cleanup.
- Do not introduce new dependencies unless explicitly requested.
- Do not enable global RAG, background automation, or autonomous governance.
- Do not write to Qdrant from retrieval paths.
- Do not cache secrets, logs, traces, JSONL streams, browser profiles, or cookies.

### Before PR or Commit

Run:

```bash
git status --short
git diff --cached --name-only
```

Confirm:

- staged files are minimal and intentional
- no forbidden paths are staged
- `.github/workflows/*` files are excluded unless separately approved
- tests relevant to the change are present and pass

## Stable Baseline Invariants

Copilot should preserve these invariants unless the user explicitly requests a scoped change:

- Render policy remains locked.
- Context Manager v1 remains active.
- Qdrant remains read-only.
- Redis retrieval cache remains conservative and opt-in.
- No global RAG auto-enable.
- No manual `rag query` command unless explicitly reintroduced.
- No new agents.
- No telemetry expansion.
- No workflow activation.
- No deployment.
- No runtime control expansion.
