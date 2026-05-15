# Retrieval Stack Runbook v0

**Mode:** Documentation only  
**Runtime impact:** None  
**Global RAG:** Disabled  
**Qdrant:** Read-only  
**Redis policy:** Unchanged

## 1. Current Retrieval Architecture

The retrieval stack is conservative and explicit. It does not enable automatic RAG for every prompt.

Components:

1. **Context Manager v1**
   - Enforces retrieval budget behavior.
   - Reduces retrieval under warning pressure.
   - Skips retrieval at block threshold.

2. **Qdrant `openclaw_knowledge`**
   - Read-only retrieval collection.
   - Stores approved low-risk knowledge chunks.
   - Must not be mutated by retrieval paths.

3. **Redis Retrieval Cache v0**
   - Optional cache for read-only retrieval results.
   - Uses TTL.
   - Caches only safe metadata and approved chunks.
   - Preserves source paths.

4. **Render Policy**
   - Locked stable render behavior.
   - `progress` must return exactly:

```text
Stable. No user action required.
```

## 2. Normal Operation

### Cache Miss

```text
request → Context Manager v1 → Redis miss → Qdrant read-only retrieval → sanitize/bound → cache safe result → return sourced result
```

Rules:

- Qdrant is read-only.
- Source paths are preserved.
- Forbidden paths are filtered.
- Token limits remain enforced.

### Cache Hit

```text
request → Context Manager v1 → Redis hit → return cached safe result → skip Qdrant
```

Rules:

- Cache hit must not call Qdrant.
- Cached chunks must retain source paths.
- Cached payload must remain bounded and safe.

### Stable Progress Render

`progress` output must remain exactly:

```text
Stable. No user action required.
```

No header, telemetry block, uptime, context percentage, RAG status, subagent state, next-state line, or emoji.

## 3. Failure Handling

### Redis Unavailable

Behavior:

```text
Redis unavailable → fall back to Qdrant read-only retrieval
```

Redis failures must not break retrieval.

### Qdrant Unavailable

Behavior:

```text
Qdrant unavailable → return retrieval unavailable / retrieval failed
```

Do not fabricate an answer from missing retrieval results.

### High Context Pressure

Behavior:

```text
warning threshold exceeded → reduce retrieval top_k
block threshold reached → skip retrieval
```

Skip message:

```text
Retrieval skipped due to context pressure.
```

### Forbidden Path Detected

Behavior:

```text
forbidden path detected → drop chunk
```

Do not cache or return chunks from forbidden paths.

### Empty Retrieval

Behavior:

```text
No relevant knowledge found.
```

No hallucinated answer should be generated from empty retrieval.

## 4. Safety Rules

- No Qdrant writes.
- No Qdrant upsert/delete/payload mutation from retrieval paths.
- No auto-memory learning.
- No global RAG auto-enable.
- No secrets cached.
- No raw logs cached.
- No traces cached.
- No JSONL streams cached.
- No browser profiles cached.
- No cookies cached.
- No retrieval telemetry spam in chat.
- Keep Context Manager v1 active.
- Keep render policy locked.

Forbidden cache/retrieval classes include:

- `.env`
- tokens or token-containing content
- `logs/`
- `traces/`
- `storage/`
- `qdrant/`
- `redis/`
- `models/`
- `*.jsonl`
- `__pycache__/`
- `*.pyc`
- `node_modules/`
- browser profiles
- cookies

## 5. Verification Commands

### Progress

User-facing check:

```text
progress
```

Expected:

```text
Stable. No user action required.
```

### Retrieval Stack Health Check

Local validation:

```bash
python3 -m pytest tests/test_context_manager_v1.py tests/test_qdrant_rag_readonly.py tests/test_redis_retrieval_cache.py tests/test_render_policy.py -q
```

Expected:

```text
all tests pass
```

### Redis Cache Check

Local check:

```bash
python3 - <<'PY'
from runtime.cache.redis_retrieval_cache import RedisRetrievalCache
cache = RedisRetrievalCache()
print(cache.redis_client_connects())
print(cache.ttl_seconds)
print(cache.max_cached_chunks_per_query)
print(cache.max_cached_total_tokens)
PY
```

Expected:

```text
True
900
5
6000
```

### Qdrant Read-Only Check

Local check:

```bash
python3 - <<'PY'
from qdrant_client import QdrantClient
from runtime.rag.qdrant_retriever import QdrantRetriever
client = QdrantClient(url='http://localhost:6333')
print('openclaw_knowledge' in [c.name for c in client.get_collections().collections])
print(all(not hasattr(QdrantRetriever, name) for name in [
    'upsert', 'delete', 'set_payload', 'delete_collection', 'upload_points'
]))
PY
```

Expected:

```text
True
True
```

## 6. Rollback Plan

If retrieval stack instability appears:

1. **Disable Redis cache path**
   - Stop using `RedisRetrievalCache` wrapper.
   - Do not delete Redis data unless separately approved.

2. **Fall back to Qdrant read-only retrieval**
   - Use `QdrantRetriever` directly.
   - Preserve read-only enforcement.

3. **Disable retrieval injection if context pressure rises**
   - Let Context Manager v1 reduce or skip retrieval.
   - Do not bypass block threshold.

4. **Keep render policy locked**
   - `progress` must continue returning exactly:

```text
Stable. No user action required.
```

5. **Do not perform unrelated cleanup**
   - No Qdrant deletion.
   - No global RAG enablement.
   - No workflow activation.
   - No new telemetry.
