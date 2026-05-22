# 🔍 Intel Search Protocol

**Owner:** @intel (Research Agent)
**Approved by:** @main
**Last updated:** 2026-05-22

**Invariants:** `PROTOCOL_INVARIANTS.md` applies when rules conflict or drift.

## Pipeline

```
@main asks question
       │
       ▼
┌─────────────────────┐
│  1. MEMORY CHECK    │ ← Qdrant vector search
│  (0.5s, free)       │   If found → return cached answer
└─────────┬───────────┘
          │ miss
          ▼
┌─────────────────────┐
│  2. GITHUB SEARCH   │ ← gh search issues/code + gh api
│  (2-5s, free)       │   Search OSS repos, issues, PRs
└─────────┬───────────┘
          │ miss
          ▼
┌─────────────────────┐
│  3. WEB DEEP SEARCH │ ← tavily_search(advanced)
│  (3-10s, API cost)  │   Deep web crawl with AI summary
└─────────┬───────────┘
          │ results
          ▼
┌─────────────────────┐
│  4. CONTENT EXTRACT │ ← tavily_extract / web_fetch
│  (2-5s per URL)     │   Full text from top results
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  5. STORE & SYNTH   │ ← qdrant_upsert() + cross-ref
│  (1s)               │   Cache for future, return to @main
└─────────────────────┘
```

## Tool Reference

### GitHub Tools (`gh` CLI)

| Command | Description |
|---------|-------------|
| `gh search issues "<query>" --repo=<owner/repo>` | Search open issues |
| `gh search code "<query>" --repo=<owner/repo>` | Search code snippets |
| `gh search repos "<query>"` | Find repos by topic |
| `gh api search/issues?q=<query>&per_page=5` | Structured API query |
| `gh issue list --repo=<owner/repo> --label=<label>` | List issues by label |

### Web Tools

| Tool | Depth | Cost | Best For |
|------|-------|------|----------|
| `tavily_search` | advanced | API call | Technical deep dives |
| `web_search` | basic | free | Quick factual lookups |
| `web_fetch` | N/A | free | Single-page extraction |
| `tavily_extract` | advanced | API call | Multi-page content |

## Caching Policy

- **Always cache** novel findings to Qdrant with `qdrant_upsert()`
- **Tag format:** `{source}_{date}_{topic}`
- **Cache TTL:** 7 days (re-verify after expiry)
- **Skip caching** for trivial lookups (time, weather, etc.)

## Result Format

```markdown
### Summary
[2-3 sentence synthesis]

### Sources
- [Source Title](url) — key takeaway
- [GitHub Issue #42](url) — related discussion
- Qdrant Knowledge Gem: `{tag_name}`

### Confidence
- **High:** 3+ sources agree, GitHub issue verified
- **Medium:** 1-2 sources, plausible
- **Low:** Speculative, needs verification
```


## External Write Guardrails

Follow `PROTOCOL_INVARIANTS.md` for all external side effects:

- Confirm user intent unless the user explicitly requested the write.
- Prefer dry-run/preview where available.
- Use idempotency or dedupe markers to avoid duplicate issues, messages, hooks, commits, or provider jobs.
- Respect `429` / `Retry-After`; use bounded backoff, never tight loops.
- Record outcome in an audit report, issue comment, git commit, or memory file when relevant.
- State rollback steps or `[blocked]` if rollback is impossible.
