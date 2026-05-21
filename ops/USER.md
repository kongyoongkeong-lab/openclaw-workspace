# User Context: Jason (The Owner)

## Ops Preferences
- **Tooling:** Jason prefers `pnpm` for Node.js and `uv` or `poetry` for Python.
- **Logging:** Always log the output of long-running commands to `~/openclaw-stack/logs/ops.log`.
- **Infrastructure:** Focus on keeping the Docker bridge stable. 
- **Approval:** Jason trusts @ops for file reads, but wants a "dry-run" summary for any `docker-compose down` actions.
- **GitHub:** Use `gh` CLI for all repo operations. PAT stored in `~/.config/gh/hosts.yml`.
- **Auto-Backup:** Runs daily via OpenClaw cron. Tags commits as `backup-YYYY-MM-DD`.

## Known Repos
- `kongyoongkeong-lab/openclaw-workspace` — Agent configs + memory
- `kongyoongkeong-lab/openclaw-config` — Gateway + infrastructure configs

## Local Paths
- Master Stack: `~/openclaw-stack`
- Configs: `~/.openclaw/`