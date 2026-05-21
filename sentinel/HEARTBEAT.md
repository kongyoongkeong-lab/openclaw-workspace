# Agent Heartbeat: @sentinel
**Scope:** Security & Hardware Safety

## Metrics to Watch
- **GPU Temp:** Alert if 4070 Ti Super hits 82°C.
- **Auth Integrity:** Check if `gateway.auth.token` has been leaked in any recent log files.
- **Hallucination Rate:** Track "Confidence Scores" from @main.

## Self-Correction
- **Security Breach:** If a destructive command is detected without @main's signature, lock the `@ops` terminal immediately.
