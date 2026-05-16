# CONTEXT_COMPRESSED Event Log
**Priority:** HIGH  
**Purpose:** Track semantic degradation during context compaction  
**Storage:** append-only JSONL pattern

---

## Event Schema

```python
ContextCompressionEvent(
    before_tokens=22000,
    after_tokens=8000,
    compression_ratio=0.36,
    entities_preserved=0.91,
    keywords_preserved=0.87,
    citations_preserved=1.00,
    semantic_retention_score=0.92,
    trigger_reason="threshold_90_percent",
    timestamp="2026-05-14T04:03:00+08:00"
)
```

---

## Heuristic Calculation

```python
semantic_retention_score = (
    entities_preserved * 0.4 +
    keywords_preserved * 0.3 +
    citations_preserved * 0.3
)

# Example:
# (0.91 * 0.4) + (0.87 * 0.3) + (1.00 * 0.3) = 0.923
```

---

## Degradation Taxonomy

```python
class DegradationReason(Enum):
    CONTEXT_PRESSURE = "Context compaction triggered"
    TOOL_TIMEOUT = "Tool invocation timeout"
    SOURCE_INSUFFICIENT = "Insufficient retrieval results"
    RETRY_LOOP = "Excessive retry attempts"
    SUMMARY_DRIFT = "Summary accuracy degradation"
    MEMORY_EVICTION = "Critical memory evicted"
```

---

## Warning Thresholds

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| `semantic_retention_score` | <0.85 | <0.80 | Governance trim |
| `compression_ratio` | >0.40 | >0.50 | Emergency compaction |
| `entities_preserved` | <0.85 | <0.80 | Entity reconciliation |

---

## First Event Example

```json
{
  "timestamp": "2026-05-14T04:03:00+08:00",
  "event_type": "CONTEXT_COMPRESSED",
  "metrics": {
    "before_tokens": 24000,
    "after_tokens": 22000,
    "compression_ratio": 0.92,
    "entities_preserved": 0.98,
    "keywords_preserved": 0.95,
    "citations_preserved": 1.00,
    "semantic_retention_score": 0.97,
    "trigger_reason": "governance_amplification"
  },
  "degradation_reason": null,
  "governance_state": {
    "SPG": "active",
    "queue_depth": 0,
    "parallel_inference_limit": 2
  }
}
```

---

**Status:** 🚀 READY FOR DEPLOYMENT  
**Next:** Observe real workload degradation patterns  