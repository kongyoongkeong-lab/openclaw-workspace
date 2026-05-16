# GitHub Copilot Instructions v1

Guide GitHub Copilot so it follows OpenClaw project rules when suggesting code, tests, docs, or GitHub changes.

## 1. Runtime Safety

- Do not add new agents unless explicitly requested.
- Do not add telemetry unless explicitly requested.
- Do not enable autonomous governance.
- Do not enable self-repair.
- Do not enable browser automation.
- Do not enable ClawHub installs.
- Do not enable global RAG automatically.
- Do not modify runtime behavior unless explicitly requested.
- Do not add deployment behavior or runtime control paths without approval.

## 2. Render Policy

- `progress` must return exactly:

```text
Stable. No user action required.
```

- Full telemetry is allowed only on:

```text
show full telemetry
```

- Full protocol is allowed only on:

```text
show full protocol
protocol show <name>
```

- Never render these blocked tokens:
  - `NO_REPLY`
  - `INTERNAL_ONLY`
  - `CONTROL_ONLY`
  - `SYSTEM_ONLY`

## 3. Context Manager

- Context Manager v1 must remain before model inference.
- Oversized prompts must be blocked before model call.
- State summary should be loaded only when needed.
- Do not dump routine context telemetry into chat.
- Preserve Context Manager v1 live guard behavior.

## 4. Retrieval Stack

- Qdrant is read-only.
- Redis cache is optional support only.
- No Qdrant writes.
- No auto-memory learning.
- No global RAG auto-enable.
- Forbidden paths must never be retrieved or cached.
- Preserve source paths for approved retrieval chunks.
- Redis cache must not cache secrets, raw logs, traces, JSONL streams, browser profiles, or cookies.

Forbidden retrieval/cache paths and content include:

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

## 5. Git Safety

- Never suggest:

```bash
git add .
```

- Use exact-file staging only:

```bash
git add exact/path/file-a exact/path/file-b
```

- Never stage:
  - `.env`
  - tokens
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

- Workflow files require explicit approval:
  - `.github/workflows/*.yml`
  - `.github/workflows/*.yaml`

## 6. Testing Expectations

- Add regression tests for render, context, retrieval, and safety behavior.
- Verify `progress` exact output after any render-related change.
- Verify normal questions are not suppressed.
- Prefer tests before implementation.
- Keep tests deterministic and scoped to the requested change.

## 7. PR Behavior

- Keep PRs minimal.
- Include only approved files.
- Do not include runtime memory files.
- Do not include generated/cache files.
- Do not include workflow files unless approved.
- Prefer small PRs with minimal file diffs.
- Avoid opportunistic cleanup.
- Confirm changed files are intentional before commit or PR.
