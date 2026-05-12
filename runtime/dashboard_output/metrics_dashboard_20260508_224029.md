# Pentagon Metrics Dashboard - Complete Report
Generated: 2026-05-08T22:40:29.668575

# Context Growth Rate Analysis

## Growth Pattern
----------------------------------------

```
Time    | Context Size | Growth Rate
------------------------------
00:00   |    256 KB    |     0.0 KB/s
00:15   |    312 KB    |     0.4 KB/s
00:30   |    524 KB    |     0.7 KB/s
00:45   |    768 KB    |     0.8 KB/s
01:00   |   1024 KB    |     0.9 KB/s
01:15   |   1280 KB    |     0.8 KB/s
01:30   |   1536 KB    |     0.8 KB/s
```

## Analysis
- Peak growth rate: 0.9 KB/s at 01:00
- Current trend: stable
- Projected context limit: 4 hours until saturation
# Cache Hit Ratio Graph

## Current Cache Ratios
----------------------------------------

### LTM Cache (Target: 70-90%)
| Time    | Hit/Miss | Ratio  |
--------------------
00:00    |    15/2  | 88.2%  |
00:30    |    18/3  | 85.7%  |
01:00    |    20/4  | 83.3%  |

### Vector Cache (Target: 60-80%)
| Time    | Hit/Miss | Ratio  |
--------------------
00:00    |    45/5  | 90.0%  |
00:30    |    42/6  | 87.5%  |
01:00    |    38/7  | 84.4%  |

## Status: ✅ HEALTHY
All caches operating within target ranges.
# Hallucination Pattern Detection

## Detection Log
----------------------------------------

### Pattern 1: Entity Substitution
Occurrence: 0
Confidence: N/A

### Pattern 2: Temporal Hallucination
Occurrence: 0
Confidence: N/A

### Pattern 3: Knowledge Invention
Occurrence: 0
Confidence: N/A

### Pattern 4: Context Drift
Occurrence: 0
Confidence: N/A

## Analysis
- No hallucination patterns detected
- All responses verified against source data
- Monitoring active
# Truncation Event Log

## Event Log
----------------------------------------

| Timestamp    | Agent  | Tokens Left | Reason       |
--------------------------------------------------
|:-|:-|:-|:-|
|2026-05-08T22:37| N/A    |      N/A    | None         |

## Current Status
- No truncation events detected
- Token budget healthy
- All agents within limits
# Latency Spike Alerts

## Current Status
----------------------------------------

### Average Latency
  intel:   0.0 ms
  ops:     0.0 ms
  comms:   0.0 ms
  sentinel: 0.0 ms

### Spike Detection
  Threshold: 500ms
  Spikes Detected: 0
  Current Spike: None

### Response Time Distribution
  P50: 0ms
  P95: 0ms
  P99: 0ms

## Status: ✅ NO SPIKES