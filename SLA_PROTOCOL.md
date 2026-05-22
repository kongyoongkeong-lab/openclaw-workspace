# 📈 SLA Monitoring Protocol — v1

**Owner:** @sentinel (Guardian)
**Scope:** Service uptime tracking, response time, availability reporting
**Updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Service Level Objectives

| Service | Target Uptime | Response Time | Check Interval |
|---------|--------------|---------------|----------------|
| OpenClaw Gateway | 99.9% | < 1s | Every heartbeat |
| Qdrant | 99.5% | < 100ms | 60s |
| Redis | 99.5% | < 10ms | 60s |
| ComfyUI | 99.0% | < 5s (API) | 60s |
| GitHub API | 99.9% | < 2s | 300s |

## Uptime Tracking

```bash
#!/bin/bash
# uptime_tracker.sh — logs service availability to GitHub-tracked reports

REPORT_DIR="$HOME/.openclaw/workspace/reports/sla"
mkdir -p "$REPORT_DIR"
DATE=$(date +%Y-%m-%d)
FILE="$REPORT_DIR/$DATE.md"

check() {
  local name=$1 cmd=$2
  if eval "$cmd" >/dev/null 2>&1; then
    echo "$(date +%H:%M) | $name | ✅ UP" >> "$FILE"
    return 0
  else
    echo "$(date +%H:%M) | $name | ❌ DOWN" >> "$FILE"
    return 1
  fi
}

echo "# SLA Report — $DATE" > "$FILE"
echo "| Time | Service | Status |" >> "$FILE"
echo "|------|---------|--------|" >> "$FILE"

check "Gateway" "systemctl --user is-active openclaw-gateway.service"
check "Qdrant" "curl -s http://localhost:6333/healthz"
check "Redis" "echo PING | redis-cli"
check "ComfyUI" "curl -s http://localhost:8188/"
check "GitHub" "gh auth status"
```

## Monthly SLA Report

```markdown
### SLA Report — 2026-05

| Service | Uptime | Downtime | SLO Met? |
|---------|--------|----------|----------|
| Gateway | 99.95% | 22m | ✅ |
| Qdrant | 99.80% | 1h 26m | ✅ |
| Redis | 99.90% | 43m | ✅ |
| ComfyUI | 99.50% | 3h 35m | ✅ |
| GitHub | 100.00% | 0m | ✅ |

**Overall: 99.83%** (Target: 99.5%) ✅
```

## Alert Thresholds

| Condition | Alert | Action |
|-----------|-------|--------|
| Service down > 5 min | 🔴 Critical | @sentinel → @comms → notify Jason |
| Service down > 30 min | 🔴 Emergency | GitHub issue + Slack |
| Response time > 2x baseline | 🟡 Warning | Log + monitor |
| Uptime < SLO target | 🟠 Review | Weekly report to @main |

## GitHub Integration

```bash
# Create monthly SLA report issue
gh issue create \
  --repo kongyoongkeong-lab/openclaw-workspace \
  --title "[SLA] Monthly Report — $(date +%Y-%m)" \
  --label "sla" \
  --body "$(cat reports/sla/$(date +%Y-%m).md)"
```


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.

## Files

| File | Purpose |
|------|---------|
| `SLA_PROTOCOL.md` | This document |
| `reports/sla/` | Daily + monthly SLA reports (git-tracked) |
| `uptime_tracker.sh` | Check script |
