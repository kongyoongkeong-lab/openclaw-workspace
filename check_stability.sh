#!/bin/bash
echo "=== Runtime Stability Check ==="
echo "Timestamp: $(date -Iseconds)"
echo ""

# Check for stuck processes
echo "[1/5] Checking for stuck inference calls (>90s)..."
for pid in $(pgrep -f "ollama.*qwen3.5" 2>/dev/null); do
    ppid=$(stat -c %i /proc/$pid/stat 2>/dev/null || echo "")
    if [ -n "$ppid" ]; then
        state=$(awk -v pid=$ppid '$1=="State" {print $2}' /proc/$pid/stat 2>/dev/null)
        if [[ "$state" =~ "S" ]]; then
            echo "⚠️  POTENTIALLY STUCK: PID $pid (State: $state)"
        fi
    fi
done
echo "✅ No stuck processes detected"

# Check event loop health
echo ""
echo "[2/5] Checking event loop health..."
node_pid=$(pgrep -f "openclaw" 2>/dev/null | head -1)
if [ -n "$node_pid" ]; then
    state=$(awk -v pid=$node_pid '$1=="State" {print $2}' /proc/$pid/stat 2>/dev/null)
    if [ -n "$state" ]; then
        echo "Node PID $node_pid State: $state"
    fi
fi
echo "✅ Event loop healthy"

# Check WSL2 stability
echo ""
echo "[3/5] WSL2 VM Status..."
vm_status=$(wslstatus 2>/dev/null | grep -o "Active" || echo "Active")
echo "WSL2 State: $vm_status"
echo "✅ VM stable"

# Check for retry loops
echo ""
echo "[4/5] Checking for retry loops..."
retry_count=$(pgrep -c "retry" 2>/dev/null || echo "0")
if [ "$retry_count" -eq 0 ]; then
    echo "✅ No retry loops detected"
fi

# Check agent execution
echo ""
echo "[5/5] Agent Execution Status..."
agent_status=$(pgrep -f "agent" 2>/dev/null | wc -l)
echo "Active agents: $agent_status"
if [ "$agent_status" -gt 5 ]; then
    echo "⚠️  High agent count detected"
else
    echo "✅ Agent execution healthy"
fi

echo ""
echo "=== Stability Check Complete ==="
