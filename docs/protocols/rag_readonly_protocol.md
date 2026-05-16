# Read-only Qdrant RAG Protocol v0

## Overview

This document defines the protocol for read-only semantic retrieval from Qdrant. The system must operate in a **deterministic** mode with strict guardrails against unauthorized writes, mutations, or data leakage.

## Version

- **Protocol Version:** 0.1 (Post-H1 conservative upgrade)
- **Runtime Mode:** Deterministic
- **Context Manager:** v1 (active)
- **Render Policy:** Locked

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                          │
│  (User Prompts / Agent Tasks)                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Context Manager v1                             │
│  - Token Budget Monitoring                                    │
│  - Warning/Block Threshold Enforcement                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│          QdrantRetriever (Read-Only Access)                   │
│  - Semantic Search                                             │
│  - Top-K Retrieval                                            │
│  - Forbidden Path Filtering                                   │
│  - Token Budget Trimming                                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Qdrant Collection (Read-Only)                    │
│  - Collection: openclaw_knowledge                             │
│  - NEVER write, upsert, delete, or mutate                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Core Configuration

### Collection Settings

| Parameter | Value | Description |
|-----------|-------|-------------|
| `collection_name` | `openclaw_knowledge` | Primary knowledge collection |
| `top_k` | `5` | Default number of results |
| `max_chunk_tokens` | `800` | Maximum tokens per chunk |
| `max_total_retrieval_tokens` | `6000` | Maximum total retrieval tokens |

### Token Budget Enforcement

The system must strictly enforce token budgets:

1. **Per-chunk limit:** `max_chunk_tokens = 800`
2. **Total retrieval limit:** `max_total_retrieval_tokens = 6000`
3. **Dynamic trimming:** If budget would be exceeded, remove lowest-ranked chunks

### Context Pressure Levels

| Threshold | Condition | Action |
|-----------|-----------|--------|
| Warning | `current_tokens > 4000` | Reduce top_k by 50% |
| Block | `current_tokens >= 7500` | Skip retrieval entirely |

---

## Retrieval Flow

### Step 1: Context Check

Before any retrieval attempt:

```python
if ContextManager.is_at_block_threshold():
    return {
        'status': 'skipped',
        'skipped': True,
        'reason': 'Retrieval skipped due to context pressure.'
    }
```

### Step 2: Top-K Limit Enforcement

```python
effective_top_k = min(top_k, 100)  # Hard cap at 100
```

### Step 3: Forbidden Path Filtering

Filter out any points with paths matching forbidden patterns:

```python
FORBIDDEN_PATHS = [
    '.env',
    'logs/',
    'traces/',
    'storage/',
    'qdrant/',
    'redis/',
    'models/',
    '*.jsonl',
    'browser',
    'cookies'
]
```

### Step 4: Token Budget Trimming

If total estimated tokens would exceed `max_total_retrieval_tokens`:

```python
sorted_chunks = sorted(chunks, key=lambda x: x['score'], reverse=True)
result_chunks = []
total_tokens = 0

for chunk in sorted_chunks:
    chunk_tokens = estimate_tokens(chunk['text'])
    if total_tokens + chunk_tokens <= max_total_retrieval_tokens:
        result_chunks.append(chunk)
        total_tokens += chunk_tokens
    else:
        break  # Budget exceeded
```

### Step 5: Return Results

```python
return {
    'status': 'success',
    'query': query,
    'results': result_chunks,
    'chunk_count': len(result_chunks),
    'total_tokens': total_tokens,
    'max_chunk_tokens': 800,
    'max_total_tokens': 6000
}
```

---

## Security Rules

### 🚫 NEVER Perform

- ❌ Write to Qdrant (no upsert, insert, append)
- ❌ Delete any points or collections
- ❌ Update point payloads or metadata
- ❌ Mutate vectors or embeddings
- ❌ Retrieve secrets, tokens, credentials
- ❌ Retrieve `.env` file contents
- ❌ Retrieve `logs/` directory contents
- ❌ Retrieve `traces/` directory contents
- ❌ Retrieve `storage/` directory contents
- ❌ Retrieve `*.jsonl` streams
- ❌ Access browser profiles or cookies
- ❌ Print Qdrant credentials to logs
- ❌ Expose raw internal memory without authorization

### ✅ ALWAYS Perform

- ✅ Verify read-only client connection
- ✅ Enforce top_k limits
- ✅ Filter forbidden paths
- ✅ Respect token budgets
- ✅ Log retrieval decisions externally
- ✅ Cite source names/file paths when available
- ✅ Report skipped retrievals with reason

---

## Error Handling

### Retrieval Errors

```python
return {
    'status': 'error',
    'error': str(exception_message),
    'results': [],
    'chunk_count': 0,
    'total_tokens': 0
}
```

### Common Error Messages

- `Collection not found` → Collection may not exist or connection failed
- `No results found` → Query returned no relevant chunks
- `Retrieval skipped due to context pressure` → Context at block threshold
- `Forbidden path filtered` → Point contained sensitive path (logged, not returned)

---

## Logging

All retrieval decisions must be logged externally (NOT to chat):

```python
logger = logging.getLogger('openclaw.rag.qdrant_retriever')
logger.info(f"Retrieved {len(chunks)} chunks (tokens: {total_tokens})")
logger.warning(f"Filtered forbidden path in retrieval")
```

---

## Test Requirements

Tests must verify:

1. ✅ `qdrant_client_imports` - qdrant_client can be imported
2. ✅ `readonly_mode_enforced` - No write methods exposed
3. ✅ `top_k_limit_enforced` - Top-k is capped at 100
4. ✅ `max_total_retrieval_tokens_enforced` - Budget trimming works
5. ✅ `forbidden_paths_filtered` - Forbidden paths are rejected
6. ✅ `no_upsert_allowed` - Upsert not available
7. ✅ `no_delete_allowed` - Delete not available
8. ✅ `context_pressure_reduces_top_k` - High context reduces results
9. ✅ `block_threshold_skips_retrieval` - Block threshold skips retrieval
10. ✅ `progress_stable` - Always returns "Stable. No user action required."

---

## Usage Example

```python
from runtime.rag.qdrant_retriever import QdrantRetriever

# Initialize retriever
retriever = QdrantRetriever(
    host='localhost',
    port=6333
)

# Perform retrieval
result = retriever.retrieve(
    query="What is the purpose of Qwen 3.5?",
    top_k=5
)

if result['status'] == 'success':
    for chunk in result['results']:
        print(f"Source: {chunk['payload'].get('source', 'unknown')}")
        print(f"Content: {chunk['text'][:200]}...")
        print("---")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

---

## Post-H1 Status

- ✅ **Mode:** Post-H1 conservative upgrade
- ✅ **Runtime:** Deterministic
- ✅ **Context Manager:** v1 (active)
- ✅ **Render Policy:** Locked
- ✅ **Governance:** O(1) complexity
- ✅ **GPU:** 86% (safe)
- ✅ **VRAM:** 81% (safe)
- ✅ **Context:** 30% idle occupancy
- ✅ **Strict H1 Validation:** ACTIVE

---

## Next Steps

- [ ] Enable automatic retrieval for eligible prompts
- [ ] Register as agent tool (optional)
- [ ] Add Redis caching layer (optional)
- [ ] Implement multi-collection support
- [ ] Add semantic filters (category, date range)

---

**Protocol Status:** 🟢 Active | **Version:** 0.1 | **Last Updated:** 2026-05-16
