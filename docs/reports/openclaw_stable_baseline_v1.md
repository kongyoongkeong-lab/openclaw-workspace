# OpenClaw Stable Baseline v1

**Mode:** Documentation/checkpoint only  
**Runtime impact:** None  
**Recorded after:** Interface Verification v1  
**Status:** Stable baseline checkpoint

## 1. Render Policy Status

Render policy is locked.

Required stable progress output:

```text
Stable. No user action required.
```

Rules:

- `progress` renders only the exact stable one-line response when no warning/failure/degradation/invariant break/user decision is present.
- Normal questions are not suppressed.
- Blocked tokens are stripped before rendering:
  - `NO_REPLY`
  - `INTERNAL_ONLY`
  - `CONTROL_ONLY`
  - `SYSTEM_ONLY`

## 2. Context Manager v1 Status

Context Manager v1 remains active.

Current verified behavior:

- Warning threshold behavior reduces retrieval scope.
- Block threshold behavior skips retrieval.
- Retrieval skip output:

```text
Retrieval skipped due to context pressure.
```

No Context Manager logic changes were made for this checkpoint.

## 3. Qdrant Read-Only Status

Qdrant read-only retrieval remains available for the `openclaw_knowledge` collection.

Verified state:

- Collection exists: `openclaw_knowledge`
- Approved low-risk points remain present.
- Retriever exposes no write/mutation methods for:
  - `upsert`
  - `delete`
  - `set_payload`
  - `delete_collection`
  - `upload_points`

Safety invariant:

- No Qdrant writes from retrieval paths.

## 4. Redis Retrieval Cache Status

Redis Retrieval Cache v0 is prepared and validated as an opt-in retrieval cache.

Verified state:

- Redis connection works.
- TTL: `900` seconds.
- Max cached chunks per query: `5`.
- Max cached total tokens: `6000`.
- Cache miss falls back to Qdrant read-only retrieval.
- Cache hit skips Qdrant.
- Source paths are preserved.
- Forbidden paths and secrets are not cached.
- Redis failure degrades gracefully.

Safety invariant:

- Redis cache does not enable global RAG.
- Redis cache does not write to Qdrant.

## 5. Retrieval Stack Runbook Status

Retrieval Stack Runbook v0 exists at:

```text
docs/runbooks/retrieval_stack_runbook.md
```

Coverage:

- Current retrieval architecture.
- Normal cache miss/hit operation.
- Failure handling.
- Safety rules.
- Verification commands.
- Rollback plan.

## 6. Git Write Safety Policy Status

Git Write Safety Policy v1 exists at:

```text
security/git_write_safety_policy.md
```

Git Upgrade Protocol v1 exists at:

```text
docs/protocols/git_upgrade_protocol.md
```

Locked git safety rules:

- Never use `git add .`.
- Use exact-file staging only.
- Run `git status --short` before staging.
- Run `git diff --cached --name-only` before commit.
- Exclude forbidden files and directories.
- Workflow files require separate approval.
- If workflow scope is missing, exclude workflow files from PRs.
- Dirty workspace changes require a clean worktree.

## 7. Interface Verification v1 Status

Interface Verification v1 completed with runtime unchanged.

Verified interfaces:

- GitHub repo status checked.
- GitHub PR/branch safety checked.
- GitHub Copilot remains developer-assist only, not runtime control.
- Telegram channel status checked.
- Discord configuration status checked where available.
- OpenClaw control desktop/dashboard response path checked.
- Gateway health checked.
- `progress` exact render verified.
- Normal questions are not suppressed.
- Blocked render tokens do not appear in output.

## 8. Current Blocked Items

The following remain blocked unless separately approved and scoped:

- global RAG auto-enable
- autonomous governance
- self-repair
- ClawHub install
- browser automation
- Discord runtime control commands
- Qdrant auto-write
- workflow changes without approval

## 9. Next Safe Upgrade Candidates

Safe candidates must remain conservative, explicitly scoped, and reversible.

Candidate list:

1. **Documentation-only consolidation**
   - Index retrieval docs, policies, and runbooks.
   - No runtime changes.

2. **Read-only verification scripts**
   - Add local validation helpers that only inspect state.
   - No writes, no workflow activation.

3. **Manual retrieval diagnostics**
   - Explicit developer-only diagnostics for cache/read-only retrieval.
   - No global RAG enablement.

4. **Interface safety audit expansion**
   - More read-only checks for configured channels.
   - No control-command expansion.

5. **Clean PR preparation**
   - Exact-file staging only.
   - Exclude workflow files unless separately approved.

## Baseline Statement

OpenClaw Stable Baseline v1 records the current stable system state after Interface Verification v1. Runtime remains unchanged.
