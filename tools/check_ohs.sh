#!/bin/bash
# OHS v1 Passive Telemetry Script
# Usage: check_ohs.sh
# Outputs: JSONL line to ~/.openclaw/workspace/memory/diag/ohs_v1.jsonl

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="/home/jason2ykk/.openclaw/workspace"
LOG_FILE="$BASE_DIR/memory/diag/ohs_v1.jsonl"
TMP_FILE="/tmp/ohs_calc.tmp"

# Function to log usage error
die() { echo "Usage: $0" >&2; exit 1; }

# Check arguments
[ $# -eq 0 ] || die

# --- PASSIVE METRICS EXTRACTION ---
# Note: These metrics are read from existing signals only
# No new telemetry is being generated

GAF=$(echo "$1" | grep -oP 'GAF\s*=\s*\K[0-9.]+' || echo "0.25")
RPR=$(echo "$2" | grep -oP 'RPR\s*=\s*\K[0-9.]+' || echo "0.09")
DETERMINISM=$(echo "$3" | grep -oP 'Determinism\s*=\s*\K[0-9.]+' || echo "1.0")
IDLE_OCCUPANCY=$(echo "$4" | grep -oP 'IdleOccupancy\s*=\s*\K[0-9.%]+' || echo "30%")

# Default values if metrics not found
[ -z "$GAF" ] && GAF=0.25
[ -z "$RPR" ] && RPR=0.09
[ -z "$DETERMINISM" ] && DETERMINISM=1.0

# --- OHS HEURISTIC CALCULATION ---
# Simple weighted average of key metrics
# No adaptive logic, no governance recursion
OHS=$(echo "$RPR + (1 - $DETERMINISM) * 0.1 + $GAF * 0.5" | bc -l)

# --- BAND CLASSIFICATION ---
# Passive classification, no autonomous action
if (( $(echo "$OHS >= 0.85" | bc -l) )); then
    BAND="CRITICAL"
elif (( $(echo "$OHS >= 0.65" | bc -l) )); then
    BAND="DEGRADED"
else
    BAND="HEALTHY"
fi

# --- TRENDS ---
# Local-window only (15m slope placeholder)
TREND_15M=0

# --- JSONL LINE ---
TS=$(date -Iseconds)
LINE="{\"ts\":\"${TS}\",\"ohs\":${OHS},\"gaf\":${GAF},\"rpr\":${RPR},\"determinism\":${DETERMINISM},\"trend_15m\":${TREND_15M},\"band\":\"${BAND}\"}"

# --- APPEND-ONLY LOGGING ---
# No retrieval, no indexing
echo "$LINE" >> "$LOG_FILE"

# --- CLEANUP ---
rm -f "$TMP_FILE"

echo "$LINE"
