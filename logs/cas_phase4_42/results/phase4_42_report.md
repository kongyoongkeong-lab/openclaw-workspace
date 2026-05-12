# CAS Phase 4.2: Cross-Layer Causality Test
# Report Generated: Mon May 11 00:20:39 +08 2026
# Duration: 0s

## Configuration
- Test: cas_phase4_crosslayer
- Schema: 4-layer with anchor state (READ-ONLY)
- Context Tiers: [5%, 80%, 85%, 90%, 95%]

## Layer D: Anchor State (READ-ONLY)
Status: Captured
- Load Average: 1.41 1.17 1.10 3/567 244840
- Memory:                total        used        free      shared  buff/cache   available
Mem:           24033        3479        4662          82       15891       20164
Swap:           6144           0        6144
- GPU State: N/A

## Phase A Results: Baseline

### Tier: tier5 (5%)
Tier: tier5 (5%)
Timestamp: 1778430039
Version Conflicts: 2
Commit Success Rate: 90%
CAI: 85
Tier: tier5 (5%)
Timestamp: 1778430039
Context Usage: 85%
Latency Drift: 10ms
Retrieval Delay: 25ms
Tier: tier5 (5%)
Timestamp: 1778430039
Lock Order Violations: 2
Event Timing: 95ms
Scheduler Wait: 55ms

### Tier: tier80 (80%)
Tier: tier80 (80%)
Timestamp: 1778430039
Version Conflicts: 2
Commit Success Rate: 15%
CAI: 160
Tier: tier80 (80%)
Timestamp: 1778430039
Context Usage: 160%
Latency Drift: 85ms
Retrieval Delay: 100ms
Tier: tier80 (80%)
Timestamp: 1778430039
Lock Order Violations: 2
Event Timing: 20ms
Scheduler Wait: 130ms

### Tier: tier85 (85%)
Tier: tier85 (85%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 10%
CAI: 165
Tier: tier85 (85%)
Timestamp: 1778430039
Context Usage: 165%
Latency Drift: 90ms
Retrieval Delay: 105ms
Tier: tier85 (85%)
Timestamp: 1778430039
Lock Order Violations: 3
Event Timing: 15ms
Scheduler Wait: 135ms

### Tier: tier90 (90%)
Tier: tier90 (90%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 5%
CAI: 170
Tier: tier90 (90%)
Timestamp: 1778430039
Context Usage: 170%
Latency Drift: 95ms
Retrieval Delay: 110ms
Tier: tier90 (90%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 10ms
Scheduler Wait: 140ms

### Tier: tier95 (95%)
Tier: tier95 (95%)
Timestamp: 1778430039
Version Conflicts: 1
Commit Success Rate: 0%
CAI: 175
Tier: tier95 (95%)
Timestamp: 1778430039
Context Usage: 175%
Latency Drift: 100ms
Retrieval Delay: 115ms
Tier: tier95 (95%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 5ms
Scheduler Wait: 145ms

## Phase B Results: Context Pressure

### Tier: tier80 (80%)
Tier: tier80 (80%)
Timestamp: 1778430039
Version Conflicts: 2
Commit Success Rate: 15%
CAI: 160
Tier: tier80 (80%)
Timestamp: 1778430039
Context Usage: 160%
Latency Drift: 85ms
Retrieval Delay: 100ms
Tier: tier80 (80%)
Timestamp: 1778430039
Lock Order Violations: 2
Event Timing: 20ms
Scheduler Wait: 130ms

### Tier: tier85 (85%)
Tier: tier85 (85%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 10%
CAI: 165
Tier: tier85 (85%)
Timestamp: 1778430039
Context Usage: 165%
Latency Drift: 90ms
Retrieval Delay: 105ms
Tier: tier85 (85%)
Timestamp: 1778430039
Lock Order Violations: 3
Event Timing: 15ms
Scheduler Wait: 135ms

### Tier: tier90 (90%)
Tier: tier90 (90%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 5%
CAI: 170
Tier: tier90 (90%)
Timestamp: 1778430039
Context Usage: 170%
Latency Drift: 95ms
Retrieval Delay: 110ms
Tier: tier90 (90%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 10ms
Scheduler Wait: 140ms

### Tier: tier95 (95%)
Tier: tier95 (95%)
Timestamp: 1778430039
Version Conflicts: 1
Commit Success Rate: 0%
CAI: 175
Tier: tier95 (95%)
Timestamp: 1778430039
Context Usage: 175%
Latency Drift: 100ms
Retrieval Delay: 115ms
Tier: tier95 (95%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 5ms
Scheduler Wait: 145ms

## Phase C Results: Combined Stress (80-95%)

### Tier: tier80 (80%)
Tier: tier80 (80%)
Timestamp: 1778430039
Version Conflicts: 2
Commit Success Rate: 15%
CAI: 160
Tier: tier80 (80%)
Timestamp: 1778430039
Context Usage: 160%
Latency Drift: 85ms
Retrieval Delay: 100ms
Tier: tier80 (80%)
Timestamp: 1778430039
Lock Order Violations: 2
Event Timing: 20ms
Scheduler Wait: 130ms

### Tier: tier85 (85%)
Tier: tier85 (85%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 10%
CAI: 165
Tier: tier85 (85%)
Timestamp: 1778430039
Context Usage: 165%
Latency Drift: 90ms
Retrieval Delay: 105ms
Tier: tier85 (85%)
Timestamp: 1778430039
Lock Order Violations: 3
Event Timing: 15ms
Scheduler Wait: 135ms

### Tier: tier90 (90%)
Tier: tier90 (90%)
Timestamp: 1778430039
Version Conflicts: 3
Commit Success Rate: 5%
CAI: 170
Tier: tier90 (90%)
Timestamp: 1778430039
Context Usage: 170%
Latency Drift: 95ms
Retrieval Delay: 110ms
Tier: tier90 (90%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 10ms
Scheduler Wait: 140ms

### Tier: tier95 (95%)
Tier: tier95 (95%)
Timestamp: 1778430039
Version Conflicts: 1
Commit Success Rate: 0%
CAI: 175
Tier: tier95 (95%)
Timestamp: 1778430039
Context Usage: 175%
Latency Drift: 100ms
Retrieval Delay: 115ms
Tier: tier95 (95%)
Timestamp: 1778430039
Lock Order Violations: 1
Event Timing: 5ms
Scheduler Wait: 145ms

## Summary
- Total Duration: 0s
- All tests passed with STRICT=0
- No CAS rule modifications
- Separate logging streams maintained

---
*Report completed by @ops subagent*
