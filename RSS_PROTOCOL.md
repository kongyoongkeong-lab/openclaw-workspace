# 📰 RSS Aggregation Protocol — v1

**Cost:** Free (RSS is an open standard)
**Owner:** @intel (Research)
**Updated:** 2026-05-22

## Architecture

```
RSS Feeds (tech blogs, news, releases)
      │
      ▼
┌──────────────────┐
│  rss_aggregator.py│ ← Periodic fetch (cron: 2h)
│  feedparser       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Qdrant Vector DB │ ← Store as knowledge gems
│  Tag: rss_{feed}  │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  @intel Search    │ ← Semantic search across feeds
│  (memory tier)    │
└──────────────────┘
```

## Default Feed List

| Feed | Topic | Priority |
|------|-------|----------|
| **Hacker News** `https://hnrss.org/frontpage` | Tech news | ⭐⭐⭐ |
| **GitHub Trending** `https://github.com/trending` | OSS discovery | ⭐⭐⭐ |
| **ArXiv CS** `http://export.arxiv.org/rss/cs` | AI/ML papers | ⭐⭐⭐ |
| **OpenClaw Releases** `https://github.com/openclaw/openclaw/releases.atom` | System updates | ⭐⭐ |
| **ComfyUI Releases** `https://github.com/comfyanonymous/ComfyUI/releases.atom` | Image gen updates | ⭐⭐ |
| **Qdrant Blog** `https://qdrant.tech/blog/rss` | Vector DB news | ⭐⭐ |

## Customization

Edit `~/.openclaw/workspace/rss_aggregator.py` to:

```python
FEEDS = [
    "https://hnrss.org/frontpage",
    "https://github.com/trending",
    # Add your own:
    "https://your-blog.com/rss",
]
```

## Data Flow

```
1. rss_aggregator.py fetches all configured RSS feeds
2. Parses each entry: title, link, summary, published date
3. Deduplicates by link hash
4. Stores new entries in Qdrant with tag: rss_{feed_name}
5. @intel finds them via qdrant_query with "rss" prefix
6. Runs every 2 hours via cron
```

## Qdrant Tag Format

```json
{
  "source": "rss",
  "feed": "hacker_news",
  "title": "OpenClaw v2026.5.18 released",
  "url": "https://github.com/openclaw/openclaw/releases/...",
  "summary": "New version with improved multi-channel support...",
  "published": "2026-05-22T01:00:00Z",
  "fetched_at": 1716339600,
  "ttl_days": 7
}
```

## Commands

```bash
# Manual fetch
python3 ~/.openclaw/workspace/rss_aggregator.py

# Show last 10 entries
python3 ~/.openclaw/workspace/rss_aggregator.py --recent

# List configured feeds
python3 ~/.openclaw/workspace/rss_aggregator.py --feeds
```

## Retention

| Data | Retention | Reason |
|------|-----------|--------|
| RSS entries in Qdrant | 7 days | News is time-sensitive |
| Fetched log | 30 days | Debug / audit |
| Dedup cache | 30 days | Prevents re-fetch |

## Files

| File | Purpose |
|------|---------|
| `RSS_PROTOCOL.md` | This document |
| `rss_aggregator.py` | Fetch + store script |
| Cron: `pentagon-rss-fetch` | Every 2 hours |
