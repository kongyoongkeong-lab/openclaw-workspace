# Runtime Stability Test (CORE SYSTEM TEST)
**Start Time:** `2026-05-09 18:26+08:00`  
**Duration:** 30-60 minutes  
**Agents:** @intel, @ops, @comms  
**Goal:** Detect freezes, event loop spikes, stalled executions, restart behavior.

## 🧪 Test Parameters
- **Concurrent Inference Calls:** 5 (max)
- **Timeout Governance:** 30s per query
- **Agent Backpressure:** Enabled
- **Parallel Task Ceiling:** 3

## 📊 Observed Metrics (Log to File)
- **Event Loop Delay:** `p50/p99` in ms
- **Retry Loops:** Count per operation
- **Stalled Executions:** > 2 triggers auto-improvement
- **System Freezes:** Any detected
- **Restart Behavior:** Cause and recovery time

## ⚠️ Auto-Improvement Triggers
If observed:
1. `eventLoopDelayP99 > 200ms` → Suggest reducing concurrent calls
2. `retry loops detected` → Increase timeout governance
3. `stalled executions > 2` → Enable agent backpressure
4. `parallel tasks > ceiling` → Lower concurrency

## 📝 Subagent Instances
- `intel-stability-test`: Web search chain (5 parallel queries)
- `ops-stability-test`: Terminal operations (CPU/MEM, I/O, stalls)
- `comms-stability-report`: Final report template

**Monitor via:** cron job `stability-monitor` (60s intervals)  
**Stop at:** `2026-05-09T19:30:00+08:00`
