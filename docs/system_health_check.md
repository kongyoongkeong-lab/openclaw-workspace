# System Health Check

Purpose: one read-only command for `服务检查` / `系统检查`.

Primary command:

```bash
python3 tools/system_health_check.py
```

Detailed report:

```bash
python3 tools/system_health_check.py --details
```

Machine-readable report:

```bash
python3 tools/system_health_check.py --json
```

## Coverage

- OpenClaw gateway config summary and loopback TCP probe.
- `openclaw gateway status` when the CLI is available.
- Docker running containers.
- Docker Compose status for `n8n/` and `docker/langfuse/`.
- n8n health endpoint.
- Redis TCP or `redis-cli ping` when available.
- Qdrant collections endpoint.
- ComfyUI system stats endpoint.
- Langfuse web endpoint.
- Model runtime snapshot via `tools/model_runtime_status.py`.
- Hugging Face preflight via `tools/huggingface_preflight.py --list-only --no-write`.
- GPU/VRAM preflight via `tools/check_gpu.sh`.
- Disk usage for the workspace and `/mnt/d`.

## Safety

- The script is read-only.
- It does not start, stop, restart, or mutate services.
- It does not write health state files.
- Command output is redacted for token-like material before being printed.
- Non-OK status is diagnostic only; remediation still requires a separate explicit command.

## Exit Codes

- `0`: no failed checks.
- `1`: warning status only when `--fail-on-warn` is set.
- `2`: one or more checks failed.
- `130`: interrupted.
