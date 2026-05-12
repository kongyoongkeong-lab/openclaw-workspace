# Agent Heartbeat: @intel
**Scope:** Retrieval & Memory

## Metrics to Watch
- **DNS Health:** Ping `api.tavily.com` every 300s.
- **Vector Latency:** If Qdrant takes >500ms to return a query, trigger a "Compact Database" command.
- **Search Failures:** If Tavily returns 403 or 500, fallback to DuckDuckGo immediately.

## Self-Correction
- **DNS Failure:** Trigger the `resolv.conf` repair script if the internet is unreachable for >60s.
