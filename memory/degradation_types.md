# Degradation Taxonomy

**Purpose:** Classify degradation types for precise governance actions  
**Version:** 1.0 (First Draft)

---

## Type Registry

| Code | Name | Description | Typical Trigger |
|------|------|-------------|-----------------|
| `CONTEXT_PRESSURE` | Context Pressure | Context compaction triggered | Context saturation > threshold |
| `TOOL_TIMEOUT` | Tool Timeout | Tool invocation exceeded | Tool execution > timeout_ms |
| `SOURCE_INSUFFICIENT` | Source Insufficient | Retrieval returned insufficient | Query returns < min_results |
| `RETRY_LOOP` | Retry Loop | Excessive retry attempts | Retry count > max_retries |
| `SUMMARY_DRIFT` | Summary Drift | Summary accuracy degradation | Semantic drift detected |
| `MEMORY_EVICTION` | Memory Eviction | Critical memory evicted | LRU eviction of important data |

---

## Governance Actions by Type

### CONTEXT_PRESSURE
- **Action:** Accept compaction cost
- **Monitor:** `semantic_retention_score` trend
- **Alarm:** Score <0.80 sustained

### TOOL_TIMEOUT
- **Action:** Increase timeout or fail fast
- **Monitor:** Timeout rate
- **Alarm:** >5% of tool calls timeout

### SOURCE_INSUFFICIENT
- **Action:** Broaden query or fallback
- **Monitor:** Empty result rate
- **Alarm:** >10% of queries return empty

### RETRY_LOOP
- **Action:** Circuit breaker activation
- **Monitor:** Retry count distribution
- **Alarm:** Retry count > threshold

### SUMMARY_DRIFT
- **Action:** Reconstruct summary from sources
- **Monitor:** Summary fidelity metrics
- **Alarm:** Drift score > threshold

### MEMORY_EVICTION
- **Action:** Cache warm-up or increase capacity
- **Monitor:** Eviction rate
- **Alarm:** Eviction of recent events

---

**Status:** 🚀 READY FOR OBSERVATION  
**Next:** Deploy to real workloads and observe pattern emergence
