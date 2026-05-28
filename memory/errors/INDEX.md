# Failure Journal Index

Last updated: 2026-05-25

## Active Prevention Rules

| Rule | Source | Status |
|---|---|---|
| Before local LLM/image/video work, run `tools/check_gpu.sh` and keep VRAM below 9,728 MiB. | `ERR-20260524-001` | active |
| Poster AI-copy timeout must degrade to deterministic copy/rendering instead of aborting the whole poster pipeline. | `ERR-20260524-001` | open |
| Poster quality tooling should support current flag names; check `--help` before using older flags. | `ERR-20260524-002` | active |
| WSL-to-PowerShell commands must protect `$` from Bash expansion and avoid reserved PowerShell variable names like `$PID`. | `ERR-20260524-003` | active |
| Treat Doubao overload as provider-side failure when upload/prompt/send succeeded; preserve artifacts and retry later. | `ERR-20260524-004` | active |
| Do not hardcode n8n auth cookies/JWTs in helper scripts; pass auth through env/session flow only. | `ERR-20260525-001` | fixed |
| For n8n PostgreSQL inspection, load `n8n/.env` and use `POSTGRES_USER`/`POSTGRES_DB`; do not assume role `n8n`. | `ERR-20260525-002` | active |
| n8n Webhook nodes must use `responseMode=responseNode` when a workflow needs to return the Respond node payload. | `ERR-20260525-003` | fixed |
| Tavily setup is not complete until `tools/tavily_key_preflight.py --check-all` finds a usable key. | `ERR-20260525-004` | open |
| Use workspace-local `tools/bin/cloudflared` before installing system packages; do not start public tunnels without explicit approval. | `ERR-20260525-005` | active |
| Do not parallelize chmod or setup commands with validation commands that depend on the resulting permissions. | `ERR-20260525-006` | mitigated |

## Monthly Logs

- `2026-05.md`

