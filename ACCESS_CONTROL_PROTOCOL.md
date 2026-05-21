# 🔐 Multi-Tenant & Access Control Protocol — v1

**Owner:** @sentinel (Guardian)
**Scope:** Permission levels, user scoping, rate limiting, audit trails
**Updated:** 2026-05-22

## Access Levels

| Level | Label | Capabilities | Assignment |
|-------|-------|-------------|------------|
| **L5** | System Owner | Full access: all agents, config, credentials, GitHub, Docker | `jason2ykk` (Jason) |
| **L4** | Senior Operator | All agents, read-only config, filtered credentials | Future: trusted users |
| **L3** | Operator | @intel + @comms only, no config access | Future: team members |
| **L2** | Observer | Read-only: HEARTBEAT.md, STATUS.md, reports | Future: monitoring |
| **L1** | Guest | Ping/status only | Future: external |

## Scope Definition

```json
{
  "user": "jason2ykk",
  "level": "L5",
  "grants": {
    "agents": ["@main", "@intel", "@ops", "@comms", "@sentinel"],
    "tools": ["exec", "gh", "docker", "write", "delete"],
    "config": ["read", "write"],
    "credentials": ["read"],
    "github": ["push", "pr", "issue"]
  }
}
```

## Enforcement Points

| Action | Guard | L5 | L4 | L3 | L2 | L1 |
|--------|-------|----|----|----|----|----|
| View HEARTBEAT | @comms | ✅ | ✅ | ✅ | ✅ | ✅ |
| Run search | @intel | ✅ | ✅ | ✅ | ❌ | ❌ |
| Execute command | @ops | ✅ | ✅ | ❌ | ❌ | ❌ |
| View credentials | @sentinel | ✅ | ⚠️ filtered | ❌ | ❌ | ❌ |
| Delete files | @ops | ✅ | ❌ | ❌ | ❌ | ❌ |
| Push to GitHub | @ops | ✅ | ❌ | ❌ | ❌ | ❌ |
| Modify config | @main | ✅ | ❌ | ❌ | ❌ | ❌ |
| Rotate API keys | @main | ✅ | ❌ | ❌ | ❌ | ❌ |

## Audit Log

Every access decision is logged:

```json
{
  "timestamp": "2026-05-22T00:41:00+08:00",
  "user": "jason2ykk",
  "level": "L5",
  "action": "gh push",
  "target": "openclaw-workspace",
  "result": "granted",
  "agent": "@ops"
}
```

## GitHub Integration

```bash
# Review access via GitHub collaborators
gh api repos/kongyoongkeong-lab/openclaw-workspace/collaborators

# Protect branches
gh api repos/kongyoongkeong-lab/openclaw-workspace/branches/master/protection \
  --method PUT \
  -f required_status_checks='{"strict":true,"contexts":["Secret Scanner","Markdown Lint"]}'
```

## Config Storage

Access control config stored at `~/.openclaw/workspace/access_control.json` (git-tracked, no secrets).

## Files

| File | Purpose |
|------|---------|
| `ACCESS_CONTROL_PROTOCOL.md` | This document |
| `access_control.json` | Role definitions (git-tracked) |
