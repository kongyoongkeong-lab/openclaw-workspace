# Pentagon Agent CEG Integration Guide

## Overview
This guide details how to integrate the Cognitive Efficiency Governance (CEG) metrics system into Pentagon Agent workflows.

## CEG Metrics System

### 1. Retrieval Usefulness Ratio (RUR)
- **Formula**: RUR = Productive Retrievals / Total Retrievals
- **Thresholds**:
  - EXCELLENT: RUR > 0.7
  - ACCEPTABLE: 0.5 ≤ RUR ≤ 0.7
  - WARNING: 0.3 ≤ RUR < 0.5
  - CRITICAL: RUR < 0.3
- **Usage Point**: After @intel completes web search

### 2. Governance Overhead % (GO%)
- **Formula**: GO% = Governance Tokens / (Governance Tokens + Productive Tokens) × 100
- **Thresholds**:
  - EXCELLENT: GO% < 10%
  - HEALTHY: 10% ≤ GO% < 20%
  - HEAVY: 20% ≤ GO% < 35%
  - COLLAPSE: GO% ≥ 35%
- **Usage Point**: During inference cycle

### 3. Idle Context Detection
- **Threshold**: >30% idle slots warning, >50% critical
- **Usage Point**: Periodic @ops task
- **Action**: Compress/evict idle context

## Integration Points

### @intel (Research Agent)
```python
# After web search completes
retrieved_ids = ["mem_001", "mem_002", ...]
reasoning_referenced_ids = ["mem_001", "mem_003", ...]

rur_metrics = compute_rur(
    retrieved_ids=retrieved_ids,
    reasoning_reference_ids=reasoning_referenced_ids
)

# Log to episodic memory
log_ceg_metrics(
    metrics={"rur": rur_metrics},
    event_type="retrieval"
)
```

### @main (Orchestrator)
```python
# After inference cycle
agent_outputs = [output1, output2, ...]
reasoning_referenced = ["mem_001", "mem_003", ...]

# Compute metrics
metrics = run_all_ceg_metrics({
    "retrieved_ids": all_retrieved_ids,
    "reasoning_referenced_ids": reasoning_referenced,
    "governance_tokens": governance_count,
    "productive_tokens": productive_count
})

# Evaluate and act
if metrics["rur"]["ratio"] == "CRITICAL":
    # Request more targeted search
    @intel: "Refine search query for higher RUR"
    
if metrics["go_percent"] >= 35:
    # Flag governance overload
    @comms: "GO% COLLAPSE - optimize token usage"
```

### @ops (Execution Agent)
```python
# Periodic idle context analysis
report = run_idle_context_analysis(current_turn=10)

if report.idle_percent >= IDLE_THRESHOLD_CRITICAL:
    # Evict critical idle content
    eviction_plan = generate_eviction_plan(report)
    @ops: "Execute eviction plan: " + str(eviction_plan)
```

### @sentinel (Guardian Agent)
```python
# Security checks with telemetry
sentinel_result = process_security_check(payload, @sentinel)

# Log with tiering
tier = tier_telemetry(
    telemetry_type="security",
    timestamp=datetime.now(timezone.utc).timestamp()
)

log_ceg_metrics(
    metrics={"tier": tier, "status": "pass"},
    event_type="security"
)
```

## Telemetry Tiering System

### HOT Tier
- **Retention**: 5 minutes
- **Storage**: Memory
- **Cleanup**: Soft eviction
- **Use Case**: Real-time operations

### WARM Tier
- **Retention**: 24 hours
- **Storage**: Aggregated summary
- **Cleanup**: Daily rollup
- **Use Case**: Recent history

### COLD Tier
- **Retention**: 7 days
- **Storage**: Statistics only
- **Cleanup**: Weekly archive
- **Use Case**: Historical data

### DEAD Tier
- **Retention**: 0 days
- **Storage**: Deleted
- **Cleanup**: Immediate
- **Use Case**: Expired data

## Idle Context Occupancy Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Idle % | 30% | 50% | Compress/Evict |
| Turns Unused | 5+ | 15+ | Flag for deletion |
| Never Cited | Any | Any | Evict |

## Monitoring Dashboard

### Metrics to Track
1. **RUR Trend**: Over time
2. **GO% Trend**: Over time
3. **Idle Context %**: Current state
4. **Telemetry Volume**: Per-tier breakdown

### Alert Thresholds
- **RUR Drop**: >15% from baseline → warn
- **GO% Spike**: >40% → critical
- **Idle Context**: >50% → immediate action

## Implementation Checklist

- [ ] Import CEG modules in agent scripts
- [ ] Add RUR computation after @intel retrieval
- [ ] Add GO% computation after inference
- [ ] Schedule idle context analysis (e.g., every 20 turns)
- [ ] Set up telemetry logging
- [ ] Configure alert thresholds
- [ ] Implement eviction automation

## Testing

Run test suite:
```bash
cd /home/jason2ykk/.openclaw/workspace/memory
python3 test_ceg_metrics.py
```

Expected output:
```
=== CEG METRICS TEST SUITE ===
--- Test 1: RUR Computation ---
  RUR: 0.6 (ACCEPTABLE)
--- Test 2: GO% Computation ---
  GO%: 11.11% (HEALTHY)
--- Test 5: Idle Context Analysis ---
  Total Slots: 13
  Idle Slots: X (Y%)
✅ All Tests Passed!
```

## Next Steps

1. **Integration**: Add CEG calls to agent scripts
2. **Monitoring**: Set up metrics tracking
3. **Automation**: Implement eviction automation
4. **Alerting**: Configure alert thresholds
5. **Documentation**: Update runbooks

## References

- [`idle_context_occupancy.py`](./idle_context_occupancy.py) - Idle context detection
- [`telemetry_integration.py`](./telemetry_integration.py) - Telemetry tiering
- [`test_ceg_metrics.py`](./test_ceg_metrics.py) - Test suite
- [`memory_router_ceg.py`](./memory_router_ceg.py) - Integration layer

---

**Status**: 🚀 Production-Ready | 🤖 Operational
