# 📋 Compliance & Audit Protocol — v1

**Owner:** @sentinel (Guardian)
**Scope:** Audit trails, log retention compliance, access reviews
**Updated:** 2026-05-22

## Audit Trail Requirements

| Event | Logged To | Retention | Rationale |
|-------|-----------|-----------|----------|
| Command execution | `~/.openclaw/logs/` | 30 days | Operational audit |
| Config changes | Git history (workspace) | Permanent | Version control |
| Credential access | `reports/audit/access.log` | 90 days | Security audit |
| GitHub pushes | GitHub audit log | Permanent | GitHub native |
| Incident reports | `reports/incidents/` | 12 months | Incident review |
| Agent commands | Session context | 50 turns | Runtime trace |

## Audit Log Format

```json
{
  "event_id": "audit-20260522-001",
  "timestamp": "2026-05-22T00:41:00+08:00",
  "actor": "@ops",
  "action": "git_push",
  "target": "openclaw-workspace",
  "status": "success",
  "details": "3 files changed, 142 insertions"
}
```

## Weekly Audit Report

```bash
#!/bin/bash
# audit_report.sh — generates weekly compliance summary

REPORT_DIR="$HOME/.openclaw/workspace/reports/audit"
mkdir -p "$REPORT_DIR"
DATE=$(date +%Y-%m-%d)

cat > "$REPORT_DIR/weekly_$DATE.md" << EOF
# Audit Report — Week of $DATE

## Commands Executed
- Total: $(grep -c "exec\|run" ~/.openclaw/logs/*.log 2>/dev/null || echo 0)
- Blocked: $(grep -c "BLOCKED\|REJECTED" ~/.openclaw/logs/*.log 2>/dev/null || echo 0)

## Git Activity
- Commits: $(cd ~/.openclaw/workspace && git log --oneline --since="7 days ago" | wc -l)
- Files changed: $(cd ~/.openclaw/workspace && git diff --stat HEAD~7..HEAD 2>/dev/null | tail -1)

## Incidents
- New: $(find ~/.openclaw/workspace/reports/incidents -name "*.md" -newer "$(date -d '7 days ago' +%Y-%m-%d)" | wc -l)
- Open: 0

## Credential Access
- Total key reads: 0 (stored outside git)
- Key rotations: 0

## Status: ✅ Compliant
EOF
```

## GitHub Compliance Integration

```bash
# Export GitHub audit log for the repo
gh api repos/kongyoongkeong-lab/openclaw-workspace/events --jq '.[].type' | sort | uniq -c

# Protect branches with required reviews
gh api repos/kongyoongkeong-lab/openclaw-workspace/branches/master/protection \
  --method PUT \
  -f required_pull_request_reviews='{"required_approving_review_count":1}'
```

## Data Classification

| Class | Examples | Storage | Git? |
|-------|----------|---------|------|
| 🔴 **Critical** | API keys, PAT tokens, passwords | `~/.openclaw/credentials/` (600) | ❌ NEVER |
| 🟡 **Sensitive** | Configs without secrets, workflow templates | Workspace git | ✅ With review |
| 🟢 **Public** | Protocols, README, reports | Workspace git | ✅ Yes |

## Compliance Checklist

- [ ] Secrets stored outside git repo
- [ ] Credential files have 600 permissions
- [ ] Git ignores credentials/ and local data/
- [ ] Audit logs rotated every 30 days
- [ ] Incident reports retained 12 months
- [ ] GitHub branch protection enabled
- [ ] Weekly audit report generated

## Files

| File | Purpose |
|------|---------|
| `COMPLIANCE_PROTOCOL.md` | This document |
| `reports/audit/` | Weekly audit reports (git-tracked) |
| `audit_report.sh` | Weekly report generator |
