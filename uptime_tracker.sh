#!/bin/bash
# SLA Uptime Tracker
REPORT_DIR="reports/sla"
mkdir -p "$REPORT_DIR"
DATE=$(date +%Y-%m-%d)
FILE="$REPORT_DIR/$DATE.md"
[ -f "$FILE" ] || echo "# SLA — $DATE" > "$FILE"

check() {
  echo "$(date +%H:%M) | $1 | $([ $? -eq 0 ] && echo '✅' || echo '❌')" >> "$FILE"
}
check "Gateway" "$(systemctl --user is-active openclaw-gateway.service 2>/dev/null)"
check "Qdrant" "$(curl -s -o /dev/null http://localhost:6333/healthz 2>/dev/null)"
check "Redis" "$(echo PING | redis-cli 2>/dev/null | grep -q PONG)"
check "ComfyUI" "$(curl -s -o /dev/null http://localhost:8188/ 2>/dev/null)"
check "GitHub" "$(gh auth status 2>/dev/null | grep -q 'Logged in')"

# Commit if modified
cd ~/.openclaw/workspace
git add reports/sla/ 2>/dev/null
git commit -m "sla: uptime check — $(date +%H:%M)" 2>/dev/null || true
