# 🛟 Disaster Recovery Protocol — v1

**Owner:** @ops (Executor)
**Scope:** Backup, restore, failover, recovery drills
**Updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Recovery Tiers

| Tier | RTO | RPO | Services |
|------|-----|-----|----------|
| **T1 — Critical** | < 15 min | < 1 hour | Gateway config, GitHub repos |
| **T2 — Important** | < 1 hour | < 24 hours | Qdrant vector DB, Redis cache |
| **T3 — Best Effort** | < 1 day | < 7 days | ComfyUI models, logs, artifacts |

## Backup Strategy

### T1: GitHub (automatic)

```bash
# Everything in git is automatically backed up
cd ~/.openclaw/workspace
git push origin master --tags  # Daily cron

cd ~/openclaw-stack/openclaw-config
git push origin master           # On config change
```

### T2: Docker Volumes (manual/daily)

```bash
#!/bin/bash
# backup_volumes.sh — snapshots Docker data volumes

BACKUP_DIR="$HOME/backups"
DATE=$(date +%Y%m%d)
mkdir -p "$BACKUP_DIR"

# Qdrant
tar -czf "$BACKUP_DIR/qdrant_$DATE.tar.gz" -C ~/openclaw-stack qdrant_data/

# Redis
tar -czf "$BACKUP_DIR/redis_$DATE.tar.gz" -C ~/openclaw-stack redis_data/

# Credentials (encrypted)
tar -czf "$BACKUP_DIR/credentials_$DATE.tar.gz" -C ~/.openclaw credentials/

echo "✅ Backups created in $BACKUP_DIR"
ls -lh "$BACKUP_DIR/"
```

### T3: ComfyUI + Logs (weekly)

```bash
tar -czf "$BACKUP_DIR/comfyui_models_$DATE.tar.gz" \
  -C ~/openclaw-stack comfyui-native/models/ 2>/dev/null

tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" \
  ~/openclaw_logs/ ~/.openclaw/logs/ 2>/dev/null
```

## Recovery Procedures

### Restore Gateway Config

```bash
cd ~/openclaw-stack/openclaw-config
git pull
cp openclaw.json ~/.openclaw/openclaw.json
systemctl --user restart openclaw-gateway.service
```

### Restore Qdrant

```bash
docker stop qdrant
rm -rf ~/openclaw-stack/qdrant_data/*
tar -xzf ~/backups/qdrant_20260522.tar.gz -C ~/openclaw-stack
docker start qdrant
```

### Full System Restore

```bash
#!/bin/bash
# restore_all.sh — full system recovery

echo "🛟 Full System Restore — $(date)"

# 1. Restore workspace from GitHub
cd ~/.openclaw/workspace
git pull --rebase

# 2. Restore config
cd ~/openclaw-stack/openclaw-config
git pull
cp openclaw.json ~/.openclaw/openclaw.json

# 3. Restart all services
~/openclaw-stack/recover_all.sh

# 4. Verify
~/openclaw-stack/health_check.sh
echo "✅ System restored"
```

## Recovery Drills

| Drill | Frequency | Duration | Success Criteria |
|-------|-----------|----------|-----------------|
| Git restore test | Weekly | 5 min | `git clone` + verify |
| Docker restart | Monthly | 10 min | All services up < 5 min |
| Full recovery | Quarterly | 30 min | Full system < 15 min |

## GitHub Issue on Failure

```bash
gh issue create \
  --repo kongyoongkeong-lab/openclaw-workspace \
  --title "[DR] Recovery drill failed — $(date +%Y-%m-%d)" \
  --label "disaster-recovery" \
  --body "## Drill Results\n**Service:** ${SERVICE}\n**Result:** ❌ FAILED\n**Time:** ${TIME}s (limit: ${LIMIT}s)"
```


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.

## Files

| File | Purpose |
|------|---------|
| `DISASTER_RECOVERY_PROTOCOL.md` | This document |
| `~/backups/` | Local backup storage (git-ignored) |
| `restore_all.sh` | Full system restore script |
