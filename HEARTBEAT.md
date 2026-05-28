# Agent Heartbeat: @main

Status: idle.
Last updated: 2026-05-22 21:37+08:00.

## Current Standing Instruction

- Do not infer or resume old tasks from prior chats.
- If no current user request requires action, reply `HEARTBEAT_OK`.
- Keep protocol/runtime remediation work explicit and user-confirmed.

## Archived Validation

- Long-Horizon Stability Phase H1 is concluded.
- Original H1 target was 2026-05-11 09:16+08:00.
- H1 no longer creates active remediation or monitoring tasks.

## Active Safety Invariants

- No production activation without explicit approval.
- No new agents without explicit approval.
- No telemetry expansion without explicit approval.
- No Qdrant writes without explicit approval.
- No workflow changes without explicit approval.
- No persistent background tasks without explicit approval.
