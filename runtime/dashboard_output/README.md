# Pentagon Real-Time Metrics Dashboard

## Overview
Continuous metrics feed generated every 30 seconds.

## Output Files
- `metrics.jsonl` - Raw telemetry data
- `metrics_*.md` - Formatted reports
- `dashboard_output/` - All generated reports

## Channels
- **Real-time metrics feed**: Active
- **Latency spike alerts**: Monitoring
- **Cache hit ratio graphs**: Active
- **Context growth rate charts**: Active
- **Hallucination pattern detection**: Active
- **Truncation event logs**: Active

## Agent Monitoring
- @intel token usage: Tracked
- @ops cache ratios: Tracked
- @comms token budget: Tracked
- @sentinel hallucination count: Tracked

## Degradation Detection
- Hallucination threshold: 0 allowed
- Cache hit ratio target: 70-90%
- Token truncation: Logged immediately
- Latency spikes: Alert threshold 500ms
