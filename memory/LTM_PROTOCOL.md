# 🧠 Long-Term Memory Protocol — v2

**Owner:** @main (Orchestrator)
**Storage:** JSONL + Qdrant + GitHub
**Updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Memory Architecture

```
HOT (current session)     ← Runtime context (last ~50 turns)
  │
  ▼
WARM (Qdrant vectors)     ← Tagged knowledge gems, searchable
  │
  ▼
COLD (GitHub repos)       ← Committed configs + daily backups
  │
  ▼
VAULT (immutable facts)   ← memory/vault.md (system baseline)
```

## Tri-Tier Storage

| Tier | Backend | Scope | Persistence |
|------|---------|-------|-------------|
| **HOT** | OpenClaw context | Current session ~50 turns | Ephemeral |
| **WARM** | Qdrant (port 6333) | Vectorized search results, research, config | Persistent (Docker volume) |
| **COLD** | GitHub repos | Committed configs, agent files, backups | Permanent (git) |
| **VAULT** | `memory/vault.md` | Immutable system facts | In-repo, versioned |

## GitHub Memory Integration

### What Gets Committed to GitHub

| Data | Repo | Frequency |
|------|------|-----------|
| Agent configs (AGENTS.md, SOUL.md, etc.) | openclaw-workspace | On change |
| Memory files (vault.md, STATUS.md, daily logs) | openclaw-workspace | On change |
| CI/workflow configs | openclaw-workspace | On change |
| Gateway config | openclaw-config | On change |
| Docker/infra config | openclaw-config | On change |
| **Full workspace snapshot** | openclaw-workspace | **Daily** (auto-backup) |

### What Stays OUT of GitHub

| Data | Location | Reason |
|------|----------|--------|
| API keys, tokens | `~/.openclaw/credentials/` | Security |
| Qdrant vector DB | `~/openclaw-stack/qdrant_data/` | Binary, ephemeral |
| Redis cache | `~/openclaw-stack/redis_data/` | Ephemeral |
| ComfyUI models | `~/openclaw-stack/models/` | Too large |
| Session context | Runtime memory | Ephemeral |

## Memory Flow

```
User provides input
  │
  ▼
┌─────────────────────────────────────┐
│ 1. HOT: Check current session       │ ← Immediate context
│    If found → continue conversation │
└──────────┬──────────────────────────┘
           │ miss
           ▼
┌─────────────────────────────────────┐
│ 2. WARM: Query Qdrant vectors       │ ← Tagged knowledge
│    If found → retrieve + cite       │
└──────────┬──────────────────────────┘
           │ miss
           ▼
┌─────────────────────────────────────┐
│ 3. COLD: Search GitHub repos (git)  │ ← Historical commits
│    git log --all --grep="keyword"   │
│    If found → reference commit      │
└──────────┬──────────────────────────┘
           │ miss
           ▼
┌─────────────────────────────────────┐
│ 4. VAULT: Read memory/vault.md      │ ← Immutable facts
│    Always available as fallback     │
└──────────┬──────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│ 5. Store new knowledge              │
│    qdrant_upsert() → tag + cache    │
│    (Auto-backed up via daily cron)  │
└─────────────────────────────────────┘
```


## Retrieval Fallback Order

Use this order before answering questions about prior work, decisions, dates, people, preferences, or todos:

1. `memory_search` across memory/wiki/session indexes.
2. If semantic search fails or quota is exhausted, read direct files: `memory/YYYY-MM-DD.md`, `memory/STATUS.md`, `memory/vault.md`, and relevant workflow/report files.
3. Search git history: `git log --since`, `git log --grep`, `git show`, and `git diff` for committed state.
4. Check visible session history when the question is conversation-specific.
5. Use GitHub/web only if local evidence is insufficient.

If semantic memory is unavailable, disclose the named blocker briefly and continue with direct file/git evidence.

## Vault Pulse (Cold Boot)

On session init, @main executes:

```python
1. Check Qdrant health → docker start if down
2. Check gh auth status → warn if expired
3. Read vault.md → adopt system baseline
4. Read STATUS.md → verify deployment state
5. Check last backup tag → verify recency
```

## Backup Protocol

```bash
# Run by OpenClaw cron every 24h
cd ~/.openclaw/workspace

# 1. Check for changes
if git status --porcelain | grep -q .; then
  # 2. Stage everything
  git add -A
  # 3. Commit with date
  git commit -m "auto-backup: backup-$(date +%Y-%m-%d)"
  # 4. Tag
  git tag -f "backup-$(date +%Y-%m-%d)"
  # 5. Push
  git push origin master --tags
fi
```

## Index Tags

Use consistent tags for Qdrant upserts:

| Tag Prefix | Content | TTL |
|------------|---------|-----|
| `research_{date}_{topic}` | Web search results | 7 days |
| `github_{date}_{repo}` | GitHub search findings | 30 days |
| `config_{date}_{file}` | Config changes | Permanent |
| `conversation_{date}` | Session summaries | 30 days |


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.
