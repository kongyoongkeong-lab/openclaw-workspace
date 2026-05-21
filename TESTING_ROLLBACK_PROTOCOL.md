# 🧪 Testing & Rollback Protocol — v1

**Owner:** @ops (Executor) + @sentinel (Guardian)
**Scope:** Pre-commit validation, dry-run deployment, safe rollback
**Updated:** 2026-05-22

## Testing Pipeline

```
Config Change (AGENTS.md, SOUL.md, etc.)
  │
  ▼
┌──────────────────────────────┐
│ 1. PRE-COMMIT CHECK           │ ← @sentinel
│    - Syntax check YAML/JSON   │
│    - Secret scan (git diff)   │
│    - Required fields present  │
└──────────┬───────────────────┘
           │ pass
           ▼
┌──────────────────────────────┐
│ 2. DRY-RUN VERIFICATION       │ ← @ops
│    - Parse changed config     │
│    - Validate agent refs      │
│    - Check for breaking refs  │
└──────────┬───────────────────┘
           │ pass
           ▼
┌──────────────────────────────┐
│ 3. COMMIT + TAG               │
│    git commit                 │
│    git tag pre-{name}         │
│    git push origin master     │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ 4. POST-DEPLOY VERIFY         │ ← 60s timer
│    - Gateway still active?    │
│    - All agents responsive?   │
│    - Services healthy?        │
└──────────┬───────────────────┘
     ┌─────┴─────┐
     ▼           ▼
   ✅ OK      ❌ FAIL
              │
              ▼
     ┌──────────────────┐
     │ 5. AUTO-ROLLBACK  │ ← git revert HEAD
     │    git revert HEAD │    Report as GitHub Issue
     │    git push        │
     └──────────────────┘
```

## Pre-Commit Validation Script

```bash
#!/bin/bash
# .git/hooks/pre-commit — installed automatically by git
# Runs before every commit to validate changes

CHANGES=$(git diff --cached --name-only)

# 1. JSON syntax check
for f in $CHANGES; do
  case "$f" in
    *.json)
      python3 -c "import json; json.load(open('$f'))" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "❌ Invalid JSON: $f"
        exit 1
      fi
      ;;
    *.yaml|*.yml)
      python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null
      if [ $? -ne 0 ]; then
        echo "❌ Invalid YAML: $f"
        exit 1
      fi
      ;;
  esac
done

# 2. Secret scan (reuse existing patterns)
if git diff --cached | grep -qE '(ghp_|gho_|sk-|comfyui-[a-f0-9]{64})'; then
  echo "❌ Secrets detected in staged changes! Aborting commit."
  exit 1
fi

# 3. Agent ref check: ensure @agent references exist
for f in $CHANGES; do
  if [[ "$f" == *.md ]]; then
    for ref in $(grep -oP '@\w+' "$f" 2>/dev/null); do
      # Allow @main, @intel, @ops, @comms, @sentinel
      case "$ref" in
        @main|@intel|@ops|@comms|@sentinel) ;;
        *) echo "⚠️  Unknown agent ref: $ref in $f" ;;
      esac
    done
  fi
done

echo "✅ Pre-commit checks passed"
```

## Rollback Flow

```bash
# Option 1: Quick revert (single commit)
git revert HEAD --no-edit
git push origin master

# Option 2: Tag rollback (full state)
git checkout pre-deploy-YYYYMMDD
git checkout -b rollback-YYYYMMDD
git push origin rollback-YYYYMMDD

# Option 3: GitHub revert via API
gh api repos/kongyoongkeong-lab/openclaw-workspace/git/refs \
  --method POST \
  -f ref="refs/heads/rollback-$(date +%Y%m%d)" \
  -f sha="$(git rev-parse pre-deploy-YYYYMMDD)"
```

## GitHub Actions: Auto-Rollback on Failure

```yaml
# .github/workflows/auto-rollback.yml
name: Auto-Rollback
on:
  push:
    branches: [master]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Dry-run parse
        run: |
          for f in $(git diff --name-only HEAD~1); do
            case "$f" in
              *.json) python3 -c "import json; json.load(open('$f'))" && echo "✅ $f" || exit 1 ;;
            esac
          done
```

## Rollback Log

```markdown
### Rollback — YYYY-MM-DD HH:MM

**Trigger:** Post-deploy verification failed
**Failed commit:** `abc1234` (feat: ...)
**Reverted to:** `def5678` (previous stable)

**Reason:**
{description}

**Status:** ✅ Reverted / ❌ Manual fix needed
```

## Files

| File | Purpose |
|------|---------|
| `TESTING_ROLLBACK_PROTOCOL.md` | This document |
| `.git/hooks/pre-commit` | Auto-installed validation hook |
| `.github/workflows/auto-rollback.yml` | CI rollback trigger |
| `reports/rollbacks/` | Rollback log directory |
