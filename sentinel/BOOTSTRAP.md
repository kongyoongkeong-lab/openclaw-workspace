# Bootstrap: @sentinel
**Sequence:** 00 (Kernel-Level)

## Boot Directives
- Hook into the `nvidia-smi` telemetry stream.
- Load security regex patterns for shell command vetting.
- Establish the **Heartbeat Monitor** for all Pentagon nodes.
- Reserve 1.5GB VRAM for emergency watchdog processing.

## Environment
- Set `SECURITY_LEVEL=strict`
- Set `HAL_CHECK=enabled` (Hallucination Detection)