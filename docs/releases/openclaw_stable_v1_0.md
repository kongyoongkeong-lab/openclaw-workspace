# OpenClaw Stable Release Snapshot v1.0

**Mode:** Documentation and Git tag preparation only  
**Runtime impact:** None  
**Git tag:** Not created automatically; user approval required  
**Workflow changes:** None  
**Status:** Recoverable stable baseline prepared

## Purpose

This snapshot marks the current verified stable OpenClaw state as a recoverable baseline.

## Stable State Checklist

### 1. Render Policy Locked

Render policy is locked.

Required `progress` output:

```text
Stable. No user action required.
```

Normal questions are not suppressed. Blocked render tokens are stripped.

### 2. Context Manager v1 Active

Context Manager v1 is active before inference.

Verified behavior:

- Context thresholds remain active.
- Oversized prompts are blocked before model call.
- Routine context telemetry is not dumped into chat.

### 3. Qdrant Read-Only Retrieval Safe

Qdrant read-only retrieval remains safe.

Verified state:

- Collection: `openclaw_knowledge`
- Retrieval path does not expose Qdrant write/mutation methods.
- Forbidden paths are filtered.
- Empty retrieval returns a safe empty result.

### 4. Redis Retrieval Cache Safe

Redis Retrieval Cache v0 remains safe.

Verified behavior:

- Cache miss falls back to Qdrant read-only retrieval.
- Cache hit skips Qdrant.
- TTL is applied.
- Source paths are preserved.
- Forbidden paths and secrets are not cached.
- Redis failure degrades gracefully.

### 5. Retrieval Stack Runbook Present

Runbook path:

```text
docs/runbooks/retrieval_stack_runbook.md
```

Coverage includes architecture, normal operation, failure handling, safety rules, verification commands, and rollback plan.

### 6. Git Write Safety Policy Present

Policy path:

```text
security/git_write_safety_policy.md
```

Protocol path:

```text
docs/protocols/git_upgrade_protocol.md
```

Key rules:

- Never use `git add .`.
- Use exact-file staging only.
- Workflow files require separate approval.
- Dirty workspaces require clean worktree discipline.

### 7. GitHub Copilot Instructions Present

Instructions path:

```text
.github/copilot-instructions.md
```

Copilot guidance preserves OpenClaw runtime safety, render policy, Context Manager v1, Qdrant read-only policy, Redis cache safety, Git safety, testing expectations, and minimal PR behavior.

### 8. Interface Verification v1 Passed

Interface Verification v1 passed with runtime unchanged.

Verified areas:

- GitHub repo and PR/branch safety.
- GitHub Copilot developer-assist-only role.
- Telegram interface status.
- Discord interface status where configured.
- OpenClaw control desktop/dashboard response path.
- Gateway health.
- Progress exact render.
- Normal questions not suppressed.
- Blocked tokens never render.

### 9. Full Stable System Verification v1 Passed

Full Stable System Verification v1 passed with runtime unchanged.

Verified areas:

- Render policy locked.
- `progress` exact output.
- Normal questions not suppressed.
- Context Manager v1 active before inference.
- Oversized prompts blocked before model call.
- Qdrant read-only retrieval safe.
- Redis retrieval cache safe.
- Required runbooks/policies/instructions present.
- Telegram, Discord, and control desktop status checked.
- Blocked tokens never render.

## Git Tag Preparation

Suggested tag name if user later approves:

```text
openclaw-stable-v1.0
```

Do not create this tag automatically.

If approved later, use exact commands only after checking workspace state:

```bash
git status --short
git tag -a openclaw-stable-v1.0 -m "OpenClaw Stable Release Snapshot v1.0"
```

Pushing the tag also requires explicit user approval.

## Blocked by Default

The following remain blocked unless separately approved and scoped:

- global RAG auto-enable
- autonomous governance
- self-repair
- ClawHub install
- browser automation
- Discord runtime control commands
- Qdrant auto-write
- workflow changes without approval

## Snapshot Statement

OpenClaw Stable Release Snapshot v1.0 is prepared as a documentation-only recoverable baseline. Runtime remains unchanged.
