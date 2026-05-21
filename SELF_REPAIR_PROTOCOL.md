# 🔧 Self-Repair Protocol — v2

**Owner:** @sentinel (Guardian) + @ops (Executor)
**Logging:** GitHub Issues + log files
**Updated:** 2026-05-22

## Failure Detection Pipeline

```
System Health Check (every heartbeat)
  │
  ├─ ✅ All OK → Continue
  │
  └─ ⚠️ Failure detected
       │
       ▼
┌───────────────────────────────────────────┐
│ 1. CLASSIFY FAILURE                        │ ← @sentinel
│    - Agent timeout (agent unresponsive)    │
│    - Service down (Qdrant/Redis/ComfyUI)   │
│    - Git push rejected                     │
│    - API rate limited (Tavily/GitHub)      │
│    - Credential expired (gh auth)          │
│    - Token leak detected (git secret scan) │
└───────────────────┬───────────────────────┘
                    │
                    ▼
┌───────────────────────────────────────────┐
│ 2. ATTEMPT AUTO-RECOVERY                   │ ← @ops
│    See recovery table below                │
│    Max 2 retries per failure type          │
└───────────────────┬───────────────────────┘
                    │
           ┌────────┴────────┐
           ▼                 ▼
     ✅ Fixed           ❌ Failed x2
        │                   │
        ▼                   ▼
┌──────────────┐   ┌──────────────────────┐
│ Log + Resume │   │ 3. ESCALATE           │ ← @main
└──────────────┘   │  - Create GitHub Issue│
                   │  - Notify @comms       │
                   │  - Log detailed trace  │
                   └──────────────────────┘
```

## GitHub Integration

### Incident Tracking via GitHub Issues

When automatic recovery fails after 2 attempts, @ops creates a GitHub issue:

```bash
gh issue create \
  --repo kongyoongkeong-lab/openclaw-workspace \
  --title "[pentagon] ${FAILURE_TYPE} — ${TIMESTAMP}" \
  --label "incident" \
  --body "
## Incident Report
**Agent:** ${AGENT}
**Type:** ${FAILURE_TYPE}
**Time:** ${TIMESTAMP}

### Attempts
1. ${RECOVERY_ATTEMPT_1} → failed
2. ${RECOVERY_ATTEMPT_2} → failed

### Log Snippet
\`\`\`
${LOG_EXCERPT}
\`\`\`

### Suggested Fix
${SUGGESTED_FIX}
"
```

### Recovery Log Storage

All recovery attempts are logged to `reports/incidents/` (git-tracked):

```
reports/incidents/
├── README.md
├── 2026-05-22_gh_auth_expired.md
└── 2026-05-21_qdrant_down.md
```

## Auto-Recovery Table

| Failure | Detect | Auto-Recovery | Escalate After |
|---------|--------|----------------|----------------|
| **Qdrant down** | curl :6333 fails → timeout | `docker start qdrant`, wait 5s, retry | 2 failures |
| **Redis down** | PING fails | `docker start redis`, wait 3s, retry | 2 failures |
| **ComfyUI down** | curl :8188 fails | `nohup python3 main.py --cpu --listen 0.0.0.0 --port 8188 &` | 2 failures |
| **gh auth expired** | `gh auth status` fails | Notify user via @comms for new token | 1 failure (human intervention) |
| **Git push rejected** | `git push` returns error | `git pull --rebase` → retry push | 2 failures |
| **API rate limited** | 429 on Tavily/GitHub | Backoff 60s → retry | 3 failures (switch sources) |
| **Agent timeout** | No response in 10s | Retry with fresh session | 2 failures (escalate to @main) |
| **Secret leaked** | git secret scan matches | Unstage file, alert @main, block commit | 1 failure (block) |

## Health Check Script

```bash
#!/bin/bash
# Run by @sentinel on each heartbeat

SERVICES=(
  "Qdrant:6333:healthz"
  "Redis:6379:PING"
  "ComfyUI:8188:/"
  "GitHub:::auth"
)

for service in "${SERVICES[@]}"; do
  IFS=':' read -r name port endpoint <<< "$service"

  case "$name" in
    Qdrant)
      curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/$endpoint" | grep -q 200 && echo "✅ $name" || echo "❌ $name"
      ;;
    Redis)
      echo "PING" | redis-cli 2>/dev/null | grep -q PONG && echo "✅ $name" || echo "❌ $name"
      ;;
    ComfyUI)
      curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/" | grep -q 200 && echo "✅ $name" || echo "❌ $name"
      ;;
    GitHub)
      gh auth status 2>&1 | grep -q "Logged in" && echo "✅ $name" || echo "❌ $name"
      ;;
  esac
done
```

## Quick Recovery Script

```bash
# Recover all services
~/openclaw-stack/recover_all.sh
```

## Integration with WORKFLOW_PROTOCOL.md

```
User Request
  │
  ▼
@main ── Analyze → Map → Dispatch
  │
  ├── ✅ Success → Response
  │
  └── ⚠️ Failure ×2
       │
       ▼
  @sentinel ── Classify → Log
       │
       ▼
  @ops ── Auto-recover (table above)
       │
       ├── ✅ Fixed → Resume
       │
       └── ❌ Still failing
            │
            ▼
       @main ── Create GitHub Issue → Notify user
```

## Failure Log Format

```markdown
### Incident: {type}
**Time:** {timestamp}
**Agent:** {agent}
**Recovery Attempts:**
1. {action} → {result}
2. {action} → {result}

**Root Cause:** {analysis}
**Resolution:** {fix applied or escalation note}
```
