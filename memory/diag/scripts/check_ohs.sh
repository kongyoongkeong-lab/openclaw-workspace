#!/usr/bin/env bash
# OHS v1 Passive Snapshot Loop
# Frozen constraints: Observation only, no scheduler hooks, non-blocking, /dev/null

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/home/jason2ykk/.openclaw/workspace/memory/diag/ohs_v1.jsonl"
ARCHIVE_DIR="/home/jason2ykk/.openclaw/workspace/memory/diag/archive"
GZIP_DIR="/home/jason2ykk/.openclaw/workspace/memory/diag/archive/compressed"
TODAY=$(date +%Y-%m-%d)

# Function: compute_ohs (passive calculation)
compute_ohs() {
  local gaf=$1
  local rpr=$2
  local det=$3
  local idle=$4
  
  if [ -z "$gaf" ] || [ -z "$rpr" ] || [ -z "$det" ] || [ -z "$idle" ]; then
    echo "Error: Missing required metrics (GAF, RPR, Determinism, IdleOccupancy)" >&2
    return 1
  fi
  
  # OHS formula: RPR*0.4 + (1-DETERMINISM)*0.1 + GAF*0.5
  # Use Python for precision (single-threaded)
  python3 -c "
import sys
gaf = float('$gaf')
rpr = float('$rpr')
det = float('$det')
idle = float('$idle')
ohs = rpr * 0.4 + (1 - det) * 0.1 + gaf * 0.5
if ohs >= 0.85:
  band = 'CRITICAL'
elif ohs >= 0.65:
  band = 'DEGRADED'
else:
  band = 'HEALTHY'
print(f'{ohs:.4f}|{band}|gaf={gaf:.2f}|rpr={rpr:.2f}|det={det:.2f}|idle={idle:.0f}%'
" 2>/dev/null
}

# Function: rotate_logs (bounded retention)
rotate_logs() {
  local now=$(date +%s)
  local keep_until=$((now - 604800))  # 7 days
  local delete_after=$((now - 2592000))  # 30 days
  
  if [ -f "$LOG_FILE" ]; then
    local mtime=$(stat -c %Y "$LOG_FILE")
    
    # Compress if older than 7 days
    if [ "$mtime" -lt "$keep_until" ]; then
      gzip -k "$LOG_FILE" 2>/dev/null || true
    fi
    
    # Cleanup files older than 30 days
    find "$ARCHIVE_DIR" -name "*.jsonl*" -type f -mtime +30 -delete 2>/dev/null || true
  fi
}

# Capture metrics (non-blocking, /dev/null redirect)
metrics=$(cat "$LOG_FILE" 2>/dev/null | tail -1 | cut -d'|' -f1-4)
gaf=${metrics:-0.25}
rpr=${metrics:-0.09}
det=${metrics:-1.0}
idle=${metrics:-30}

# Compute OHS
ohs=$(compute_ohs "$gaf" "$rpr" "$det" "$idle")
echo "OHS Snapshot: $ohs" >&2

# Append-only write (single-threaded, deterministic)
echo "$(date -Iseconds)|GAF=$gaf|RPR=$rpr|DET=$det|IDLE=$idle|OHS=$ohs" >> "$LOG_FILE" 2>/dev/null || true

# Bounded retention
rotate_logs 2>/dev/null || true

exit 0
