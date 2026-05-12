# Agent Heartbeat: @comms
**Scope:** Output & Notification Uptime

## Metrics to Watch
- **Telegram Webhook:** Monitor for "401 Unauthorized" or "404 Not Found" errors.
- **UI Connectivity:** Check if the WebSocket (`ws://127.0.0.1:18789`) is receiving "Tick" events.
- **Message Queue:** Alert if >5 messages are backed up in the outgoing buffer.

## Self-Correction
- **Telegram Down:** Switch to local file-based logging (`~/openclaw-stack/alerts.txt`) and wait for reconnection.
