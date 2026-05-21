# 📊 Log Retention Protocol — v1

**Owner:** @ops (Executor)
**Scope:** Log rotation, compression, GitHub export
**Updated:** 2026-05-22

## Log Locations

| Path | Contents | Size | Retention |
|------|----------|------|-----------|
| `~/openclaw_logs/` | Gateway troubleshooting, webhook logs | ~1.4M | 30 days |
| `~/.openclaw/logs/` | OpenClaw runtime logs | ~1.5M | 30 days |
| `~/.openclaw/workspace/reports/incidents/` | Incident reports | < 1M | 12 months |
| `~/.openclaw/workspace/reports/extracted/` | Extracted PDF data | < 1M | Monthly summary |

## Logrotate Configuration

```bash
# /etc/logrotate.d/pentagon
# Install with: sudo cp /tmp/pentagon-logrotate /etc/logrotate.d/

/home/jason2ykk/openclaw_logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}

/home/jason2ykk/.openclaw/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
}

/home/jason2ykk/.openclaw/workspace/reports/incidents/*.md {
    monthly
    rotate 12
    compress
    missingok
    notifempty
}
```

## Manual Log Rotation

If logrotate is not available, use this script:

```bash
#!/bin/bash
# Manual log rotation — run via cron weekly
LOG_DIRS=(
  "$HOME/openclaw_logs"
  "$HOME/.openclaw/logs"
)

for dir in "${LOG_DIRS[@]}"; do
  for log in "$dir"/*.log; do
    [ -f "$log" ] || continue
    # Compress if older than 7 days and > 1MB
    if [ "$(stat -c%s "$log" 2>/dev/null)" -gt 1048576 ] && \
       [ "$(find "$log" -mtime +7 -print 2>/dev/null)" ]; then
      gzip -f "$log"
      echo "  ✅ Compressed: $log"
    fi
  done
done
```

## GitHub Log Export

Weekly export of incident reports to GitHub:

```bash
# Run weekly via cron
cd ~/.openclaw/workspace

# Check for new incidents
if git status --porcelain reports/incidents/ | grep -q .; then
  git add reports/incidents/
  git commit -m "logs: export incident reports — $(date +%Y-%m-%d)"
  git push origin master
  echo "✅ Incident reports exported to GitHub"
fi
```

## Retention Schedule

| Log Type | Retention | Action After |
|----------|-----------|--------------|
| Runtime logs (.log) | 30 days | `logrotate` → compressed, auto-purged |
| Incident reports (.md) | 12 months | Git history → manual purge if needed |
| Extracted data (.json) | Indefinite | Git-tracked, manual cleanup |
| Old backups (.gz) | 90 days | Auto-purged by logrotate |
| Webhook history | 30 days | Auto-purged |

## Log Export to GitHub

To export a snapshot of all logs (including compressed archives):

```bash
tar -czf ~/openclaw-stack/log_export_$(date +%Y%m%d).tar.gz \
  ~/openclaw_logs/ \
  ~/.openclaw/logs/ \
  ~/.openclaw/workspace/reports/incidents/

# Store export in git LFS or external storage (not in workspace repo)
```

## Files

| File | Purpose |
|------|---------|
| `/etc/logrotate.d/pentagon` | logrotate config (needs sudo) |
| `~/.openclaw/workspace/LOG_RETENTION_PROTOCOL.md` | This document |
| `~/.openclaw/workspace/reports/logs/` | Exported log summaries |
