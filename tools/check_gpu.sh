#!/usr/bin/env bash
set -euo pipefail

CEILING_MIB="${OPENCLAW_VRAM_CEILING_MIB:-9728}"

if ! command -v nvidia-smi >/dev/null 2>&1; then
  echo "gpu_status=unavailable reason=nvidia-smi-missing"
  exit 2
fi

line="$(
  nvidia-smi \
    --query-gpu=name,memory.total,memory.used,utilization.gpu \
    --format=csv,noheader,nounits \
  | head -n 1
)"

IFS=',' read -r raw_name raw_total raw_used raw_util <<< "$line"
name="$(echo "$raw_name" | xargs)"
total_mib="$(echo "$raw_total" | xargs)"
used_mib="$(echo "$raw_used" | xargs)"
util_pct="$(echo "$raw_util" | xargs)"

echo "gpu_name=${name}"
echo "vram_total_mib=${total_mib}"
echo "vram_used_mib=${used_mib}"
echo "gpu_utilization_pct=${util_pct}"
echo "vram_hard_ceiling_mib=${CEILING_MIB}"

if [ "$used_mib" -gt "$CEILING_MIB" ]; then
  echo "gpu_status=blocked reason=vram_above_ceiling"
  exit 1
fi

echo "gpu_status=ok"
