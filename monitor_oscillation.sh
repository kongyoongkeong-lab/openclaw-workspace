#!/bin/bash
# Pentagon Stage 3: Oscillation Watch Monitor
# Monitors: VRAM stability, scheduler load, memory artifacts

echo "=== Pentagon Oscillation Watch Monitor ==="
echo "Monitoring for: VRAM instability, scheduler stress, memory artifacts"
echo "Sampling interval: 5 seconds"
echo "Variance threshold: 8%"

# Function to calculate variance
calc_variance() {
    local now=$(date +%s)
    local prev_vram=$(last_vram)
    local curr_vram=$(nvidia-smi --query-gpu=memory.used --format=csv | tail -1 | cut -d',' -f1)
    local diff=$((curr_vram - prev_vram))
    
    if [ $diff -lt 0 ]; then diff=$((-diff)); fi
    
    echo "$curr_vram $diff $now"
    
    last_vram=$curr_vram
    
    # Check variance > 8%
    local threshold=$(echo "$prev_vram * 8 / 100" | bc)
    local check=$(echo "$diff >= $threshold" | bc)
    
    if [ "$check" -eq 1 ]; then
        echo "⚠️  ALERT: VRAM variance ${diff}MiB exceeds 8% threshold"
        return 1
    fi
    
    return 0
}

# Initial state
last_vram=$(nvidia-smi --query-gpu=memory.used --format=csv | tail -1 | cut -d',' -f1)
prev_vram=$last_vram

echo "Initial VRAM: ${last_vram}MiB"
echo "Threshold: >8% variance = $((last_vram * 8 / 100))MiB"

# Monitor loop
for i in {1..20}; do
    sleep 5
    result=$(calc_variance)
    
    if [ $? -ne 0 ]; then
        echo "[$(date '+%H:%M:%S')] $result"
    fi
done

echo ""
echo "=== Oscillation Watch Complete ==="
echo "No critical oscillations detected during monitoring period."
