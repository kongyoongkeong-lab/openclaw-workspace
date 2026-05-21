# 📝 Notion Integration Protocol — v1

**Cost:** Free (Notion API, no paid plan required)
**Owner:** @intel (Research)
**Updated:** 2026-05-22

## Architecture

```
Notion Pages / Databases
      │
      ▼
┌──────────────────┐
│  notion_sync.py   │ ← Periodic sync (cron: 6h)
│  Read pages via   │
│  Notion API       │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Qdrant Vector DB │ ← Store as knowledge gems
│  Tag: notion_{id} │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  @intel Search    │ ← Semantic search across notes
│  (memory tier)    │
└──────────────────┘
```

## Setup

### 1. Create a Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click **"New integration"**
3. Name: `Pentagon Intel`
4. Select workspace → Submit
5. **Copy the "Internal Integration Secret"** (starts with `ntn_...`)
6. Share target pages/databases with the integration:
   - Open the page in Notion
   - Click **••• (top-right) → Add connections**
   - Select `Pentagon Intel`

### 2. Store API Token

```bash
mkdir -p ~/.openclaw/credentials
cat > ~/.openclaw/credentials/notion.json << 'EOF'
{
  "token": "ntn_your_integration_token_here",
  "stored_at": "2026-05-22"
}
EOF
chmod 600 ~/.openclaw/credentials/notion.json
```

### 3. Sync Script

```bash
# Manual sync
python3 ~/.openclaw/workspace/notion_sync.py

# Check sync status
python3 ~/.openclaw/workspace/notion_sync.py --status
```

## Notion Data Flow

```
1. notion_sync.py fetches pages from shared databases/pages
2. Extracts title + plain text content
3. Chunks text into ~1000-token segments
4. Stores in Qdrant with tags: notion_{page_id}
5. @intel finds them via qdrant_query for "notion" prefix
6. Daily sync via cron (every 6h)
```

## Data Classification

| Data Type | Stored in Qdrant? | Stored in Git? | Notes |
|-----------|-------------------|----------------|-------|
| Page titles | ✅ Yes | ❌ No | Searchable in memory |
| Page content | ✅ Yes | ❌ No | Chunked + vectorized |
| Database rows | ✅ Yes | ❌ No | Each row as separate chunk |
| API token | ❌ No | ❌ No | In `~/.openclaw/credentials/` |

## Files

| File | Purpose |
|------|---------|
| `NOTION_PROTOCOL.md` | This document |
| `notion_sync.py` | Sync script (fetch → Qdrant) |
| `~/.openclaw/credentials/notion.json` | API token (git-ignored) |
| Cron: `pentagon-notion-sync` | Every 6 hours |

## Commands

```bash
# Fetch once
python3 ~/.openclaw/workspace/notion_sync.py

# Search synced content
python3 -c "
import json
# Qdrant search for notion content
from qdrant_client import QdrantClient
client = QdrantClient('localhost', 6333)
results = client.scroll(collection_name='pentagon_brain',
    scroll_filter={'must': [{'key': 'source', 'match': {'value': 'notion'}}]},
    limit=5)
print(f'Found {len(results[0])} Notion pages')
"
```
