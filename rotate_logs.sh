#!/bin/bash
# Manual log rotation — run via cron weekly
# No sudo needed — uses gzip on user-owned files
echo "🔄 Pentagon Log Rotation — $(date)"

LOG_DIRS=(
  "$HOME/openclaw_logs"
  "$HOME/.openclaw/logs"
)
ROTATED=0

for dir in "${LOG_DIRS[@]}"; do
  [ -d "$dir" ] || continue
  for log in "$dir"/*.log; do
    [ -f "$log" ] || continue
    SIZE=$(stat -c%s "$log" 2>/dev/null || stat -f%z "$log" 2>/dev/null)
    if [ "$SIZE" -gt 1048576 ] && [ "$(find "$log" -mtime +7 -print 2>/dev/null)" ]; then
      gzip -f "$log"
      echo "  ✅ Compressed: $(basename "$log") ($SIZE bytes → $(stat -c%s "$log.gz" 2>/dev/null || echo '?') bytes)"
      ROTATED=$((ROTATED + 1))
    fi
  done
done

echo "✅ Rotation complete — $ROTATED files compressed"
