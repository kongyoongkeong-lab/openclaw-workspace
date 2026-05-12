#!/bin/bash
# GPU VRAM Check for PCG Stress Test
# Returns: VRAM usage in GB (float), status, warning flags

NVIDIA_SMI="/usr/bin/nvidia-smi"

if [[ ! -f "$NVIDIA_SMI" ]]; then
    echo "ERROR: nvidia-smi not found"
    exit 1
fi

# Get VRAM usage
VRAM_OUTPUT=$("$NVIDIA_SMI" --query-gpu=memory.used,memory.total --format=csv,noheader,nounits)
VRAM_USED=$(echo "$VRAM_OUTPUT" | cut -d',' -f1)
VRAM_TOTAL=$(echo "$VRAM_OUTPUT" | cut -d',' -f2)

# Convert to GB
VRAM_USED_GB=$(echo "scale=2; $VRAM_USED / 1024" | bc)
VRAM_TOTAL_GB=$(echo "scale=2; $VRAM_TOTAL / 1024" | bc)

# Calculate percentage
USAGE_PCT=$(echo "scale=1; $VRAM_USED_GB * 100 / $VRAM_TOTAL_GB" | bc)

echo "VRAM: ${VRAM_USED_GB}GB/${VRAM_TOTAL_GB}GB (${USAGE_PCT}%)"

# WSL2 safety check
if (( $(echo "$USAGE_PCT > 95" | bc -l) )); then
    echo "⚠️ WARNING: High VRAM usage (>95%) - burst mode allowed but monitor"
    exit 1
fi

if (( $(echo "$USAGE_PCT > 90" | bc -l) )); then
    echo "📊 High VRAM usage detected - control active"
    exit 0
fi

exit 0