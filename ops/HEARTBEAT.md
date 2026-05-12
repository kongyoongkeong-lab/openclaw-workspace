# Agent Heartbeat: @ops
**Scope:** System & Code Runtime

## Metrics to Watch
- **Process Hangups:** Monitor PIDs spawned by `terminal_execute`. Kill any process exceeding 600s.
- **Disk I/O:** Ensure the `/workspace` partition has >2GB free.
- **Python Health:** Check for `ImportError` or `ModuleNotFoundError` during skill execution.

## Self-Correction
- **Environment Drift:** If `pnpm` or `pip` fail, run a `clean-install` on the local project directory.
