# Redis Retrieval Cache Protocol v0

**Mode:** Conservative upgrade  
**Runtime:** Deterministic  
**Activation:** Opt-in only  
**Global RAG:** Disabled  
**Qdrant:** Read-only

## Goal

Cache read-only Qdrant retrieval results to reduce repeated retrieval latency while preserving deterministic behavior and safety boundaries.

## Non-Goals

This protocol does not:

- enable automatic RAG for every prompt
- write to Qdrant
- add memory self-learning
- add autonomous governance
- add agents
- add browser automation
- use ClawHub
- activate workflow files

## Defaults

| Setting | Value |
|---|---:|
| `default_ttl_seconds` | `900` |
| `max_cached_chunks_per_query` | `5` |
| `max_cached_total_tokens` | `6000` |
| `max_chunk_tokens` | `800` |

## Cache Key

Cache keys must include:

- normalized query hash
- Qdrant collection name
- effective `top_k`

Pattern:

```text
openclaw:rag:v0:<collection>:top_k=<top_k>:q=<sha256(normalized_query)>
```

## Cacheable Data

Only cache safe retrieval data:

- approved chunk text
- source path
- chunk id
- approved batch marker
- score
- bounded token metadata

Preserve source paths for auditability.

## Never Cache

Do not cache:

- forbidden paths
- secrets
- raw logs
- traces
- JSONL streams
- browser profiles
- cookies
- raw Qdrant vectors
- Redis internals

Forbidden path classes include:

- `.env`
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

## Retrieval Flow

1. Check Context Manager v1.
2. If block threshold is reached, skip retrieval and return:

```text
Retrieval skipped due to context pressure.
```

3. If warning threshold is exceeded, reduce `top_k`.
4. Compute deterministic cache key.
5. On cache hit, return cached safe payload and do not call Qdrant.
6. On cache miss, call read-only Qdrant retrieval.
7. Sanitize and bound result.
8. Cache safe payload with TTL.
9. Return retrieval result.

## Failure Behavior

Redis failure must not break retrieval.

- Redis connect failure → direct Qdrant read-only retrieval
- Redis get failure → direct Qdrant read-only retrieval
- Redis set failure → return Qdrant result without cache
- Invalid cached payload → cache miss behavior

## Safety Invariants

- Qdrant remains read-only.
- Cache is opt-in only.
- Context Manager v1 remains active.
- Render policy remains locked.
- Progress output remains exactly:

```text
Stable. No user action required.
```
