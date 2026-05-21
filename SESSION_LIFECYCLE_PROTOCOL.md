# 🔄 Session Lifecycle Protocol — v1

**Owner:** @main (Orchestrator)
**Scope:** Session creation, expiry, cleanup, optimization
**Updated:** 2026-05-22

## Session Types

| Type | Created By | Purpose | TTL | Cleanup |
|------|------------|---------|-----|---------|
| **Main** | OpenClaw Gateway | Primary user interaction | Active until idle 1h | Auto-close |
| **Sub-agent** | `sessions_spawn()` | Isolated agent tasks | Task completion + 5min | GC after task |
| **Cron** | `cron.add()` | Scheduled backups/logs | Task completion | Auto-cleanup |
| **Webhook** | Webhook receiver | External event handling | Request/response | Instant |

## Lifecycle Diagram

```
            ┌──────────┐
            │  Created  │ ← Spawned by @main or cron or webhook
            └────┬─────┘
                 │
                 ▼
            ┌──────────┐
            │  Running  │ ← Task in progress
            └────┬─────┘
                 │
           ┌─────┴──────┐
           ▼            ▼
     ┌─────────┐  ┌──────────┐
     │ Completed│  │  Timed   │ ← Timeout exceeded
     └────┬────┘  │  Out     │
          │       └────┬─────┘
          ▼            ▼
     ┌──────────────────────┐
     │  Cleanup              │ ← Kill session, free resources
     └──────────────────────┘
```

## Session Hierarchy

```
Main Session (@main)
  ├── Sub-agent: @intel (isolated)
  │     └── Qdrant connection
  ├── Sub-agent: @ops (isolated)
  │     └── Docker socket
  ├── Sub-agent: @comms (isolated)
  │     └── Telegram bot connection
  └── Sub-agent: @sentinel (isolated)
        └── Health check handles

Cron Sessions (isolated)
  ├── workspace-auto-backup (24h)
  ├── pentagon-log-rotation (7d)
  └── (future: health check, sla report)

Webhook Sessions (ephemeral)
  └── Per-request handler
```

## Timeout Configuration

| Session Type | Default Timeout | Configurable? | Action on Timeout |
|-------------|----------------|---------------|-------------------|
| Main (user) | 1h idle | Yes | Auto-close, log |
| @intel task | 120s | `timeoutSeconds` | Log + retry |
| @ops task | 120s | `timeoutSeconds` | Log + retry |
| @comms task | 60s | `timeoutSeconds` | Log + retry |
| @sentinel task | 30s | `timeoutSeconds` | Log, assume OK |
| Cron backup | 120s | Yes | Log, retry next cycle |
| Webhook | 5s | No | Log, drop event |

## Cleanup Strategy

```bash
#!/bin/bash
# session_cleanup.sh — kill stale sessions, free resources
# Run via cron or on demand

echo "🔍 Session Cleanup — $(date)"
CLEANED=0

# 1. List all subagent sessions
for session in $(openclaw sessions list --kind subagent 2>/dev/null | grep -oP '^\S+' 2>/dev/null); do
  AGE=$(openclaw sessions status "$session" 2>/dev/null | grep -oP 'Age: \K\d+')
  # Kill sessions older than 30 minutes
  if [ "$AGE" -gt 30 ] 2>/dev/null; then
    openclaw sessions kill "$session" 2>/dev/null && echo "  🧹 Killed stale: $session (${AGE}m)" && CLEANED=$((CLEANED+1))
  fi
done

# 2. Report
if [ "$CLEANED" -eq 0 ]; then
  echo "  ✅ No stale sessions"
else
  echo "  🧹 Cleaned $CLEANED stale sessions"
fi
```

## GitHub Integration

```bash
# Log session stats to GitHub
cd ~/.openclaw/workspace
cat > reports/sessions/$(date +%Y-%m-%d).md << EOF
# Session Report — $(date +%Y-%m-%d)

## Active Sessions
- Main: $(openclaw sessions list --kind main 2>/dev/null | wc -l)
- Sub-agents: $(openclaw sessions list --kind subagent 2>/dev/null | wc -l)
- Cron: $(openclaw sessions list --kind cron 2>/dev/null | wc -l)

## Performance
- Avg task latency: N/A
- Stale sessions cleaned: 0
EOF

git add reports/sessions/
git commit -m "sessions: daily report — $(date +%Y-%m-%d)"
git push origin master
```

## Best Practices

1. **Always set `timeoutSeconds`** on `sessions_spawn()` — never leave unbounded
2. **Use `cleanup="delete"`** for one-shot tasks
3. **Use `context="isolated"`** (default) — never fork unless session state required
4. **Cron sessions should be fire-and-forget** — use `sessionTarget="isolated"`
5. **Log session errors** to `reports/incidents/` for review

## Files

| File | Purpose |
|------|---------|
| `SESSION_LIFECYCLE_PROTOCOL.md` | This document |
| `session_cleanup.sh` | Stale session cleaner |
| `reports/sessions/` | Daily session stats |
