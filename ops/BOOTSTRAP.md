# Bootstrap: @ops
**Sequence:** 02 (Sub-Process)

## Boot Directives
- Check Docker socket availability (`/var/run/docker.sock`).
- Verify `gh auth status` — ensure GitHub API & git access.
- Verify `gh --version` — git credential helper configured.
- Initialize Python 3.11 virtual environment in `~/.openclaw/venv/ops`.
- Check backup cron is active: `cron list | grep workspace`.
- Clear temporary lock files in `~/.openclaw/tmp/`.

## Environment
- Set `SHELL=/usr/bin/bash`
- SET EXECUTION_MODE=direct
- Set `GITHUB_ENABLED=true`
- Set `GH_CREDENTIAL_HELPER=gh auth git-credential`

## GitHub Repos Tracked
| Repo | Purpose | Branch |
|------|---------|--------|
| `openclaw-workspace` | Agent configs + memory | master / develop |
| `openclaw-config` | Gateway + infra configs | master |

## Known Services
| Service | Port | Docker |
|---------|------|--------|
| ComfyUI | 8188 | ❌ (native process) |
| Qdrant | 6333 | ✅ qdrant/qdrant |
| Redis | 6379 | ✅ redis:7-alpine |