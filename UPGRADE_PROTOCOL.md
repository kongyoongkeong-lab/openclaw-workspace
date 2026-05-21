# 📦 Upgrade & Migration Protocol — v1

**Owner:** @main (Orchestrator)
**Scope:** Git-based upgrades, config migration, rollback
**Updated:** 2026-05-22

## Upgrade Flow

```
1. REVIEW CHANGES
   │  gh pr diff master...develop
   │  Identify breaking changes
   ▼

2. BACKUP CURRENT STATE
   │  git tag pre-upgrade-YYYY-MM-DD
   │  cp openclaw.json openclaw.json.pre-upgrade
   ▼

3. APPLY UPGRADE
   │  git checkout master
   │  git pull --rebase
   │  Merge develop → master (if applicable)
   ▼

4. VERIFY
   │  gh auth status
   │  systemctl --user is-active openclaw-gateway
   │  Check each service: Qdrant, Redis, ComfyUI
   ▼

5. COMMIT UPGRADE
   │  git tag upgrade-YYYY-MM-DD
   │  git push origin master --tags
   ▼

6. LOG
   │  Record in reports/upgrades/YYYY-MM-DD.md
```

## Migration Types

### Config Migration

```bash
# Before changing openclaw.json
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.pre-upgrade

# After changes, sync to config repo
cp ~/.openclaw/openclaw.json ~/openclaw-stack/openclaw-config/
cd ~/openclaw-stack/openclaw-config
git diff
git commit -m "migrate: {description}"
git push origin master
```

### Agent Config Migration

```bash
# Before modifying agent files
cd ~/.openclaw/workspace
git tag pre-migration-$(date +%Y%m%d_%H%M)
git push origin --tags

# After changes
git add .
git commit -m "migrate: {agent} — {description}"
git push origin master
```

## Rollback Procedure

```bash
# Option 1: Git revert (config only, no data loss)
git revert HEAD --no-edit
git push origin master

# Option 2: Tag rollback (full workspace state)
git checkout pre-upgrade-YYYY-MM-DD
git checkout -b rollback-YYYY-MM-DD
git push origin rollback-YYYY-MM-DD
```

## Breaking Change Detection

| Change Type | Risk | Rollback Action |
|-------------|------|-----------------|
| AGENTS.md modification | Low | `git revert` |
| openclaw.json rewrite | Medium | Restore `.pre-upgrade` backup |
| Docker compose change | Medium | Revert to previous image |
| GitHub Actions change | Low | `git revert` |
| Credential rotation | High | Restore from `credentials/` backup |

## Upgrade Log Template

```markdown
### Upgrade Log — YYYY-MM-DD

**Type:** Config / Agent / Docker / Workflow
**Author:** @ops
**Pre-upgrade tag:** `pre-upgrade-YYYY-MM-DD`

### Changes
- {change 1}
- {change 2}

### Verification
- Gateway: ✅ active
- Qdrant: ✅ 200
- Redis: ✅ PONG
- ComfyUI: ✅ 200
- GitHub: ✅ synced

### Status: ✅ Successful / ⚠️ Rolled back
```
