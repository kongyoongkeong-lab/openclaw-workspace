# Bootstrap: @ops
**Sequence:** 02 (Sub-Process)

## Boot Directives
- Verify `sudo` privileges for terminal execution.
- Check Docker socket availability (`/var/run/docker.sock`).
- Initialize Python 3.11 virtual environment in `~/.openclaw/venv/ops`.
- Clear temporary lock files in `~/.openclaw/tmp/`.

## Environment
- Set `SHELL=/usr/bin/bash`
- SET EXECUTION_MODE=direct
- SET TERMINATE_ON_STDOUT=true