# Bootstrap: @sentinel
**Sequence:** 00 (Kernel-Level)

## Boot Directives
- Load security regex patterns for shell command vetting.
- Establish the **Heartbeat Monitor** for all Pentagon nodes.

## Environment
- Set `SECURITY_LEVEL=strict`
- Set `HAL_CHECK=enabled` (Hallucination Detection)