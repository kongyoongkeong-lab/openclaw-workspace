#!/usr/bin/env python3
"""Redis Retrieval Cache v0.

Conservative opt-in cache wrapper for read-only Qdrant retrieval results.
No global RAG enablement. No Qdrant writes. Cache failures degrade to direct retrieval.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, Optional

try:  # Optional dependency; tests inject a fake client.
    import redis  # type: ignore
except Exception:  # pragma: no cover - dependency may be absent in minimal envs
    redis = None

try:
    from runtime.rag.qdrant_retriever import ContextManager, QdrantRetriever
except ImportError:  # pragma: no cover - direct script fallback
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(ROOT / "runtime" / "rag"))
    from qdrant_retriever import ContextManager, QdrantRetriever  # type: ignore


DEFAULT_TTL_SECONDS = 900
MAX_CACHED_CHUNKS_PER_QUERY = 5
MAX_CACHED_TOTAL_TOKENS = 6000
CACHE_PREFIX = "openclaw:rag:v0"

SECRET_PATTERNS = [
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/", re.I),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(r"(?i)(api[_\s-]?key|secret|token|password)\s*[:=]\s*['\"]?\S+"),
]


class RedisRetrievalCache:
    """Opt-in Redis cache for safe read-only retrieval results."""

    default_ttl_seconds = DEFAULT_TTL_SECONDS
    max_cached_chunks_per_query = MAX_CACHED_CHUNKS_PER_QUERY
    max_cached_total_tokens = MAX_CACHED_TOTAL_TOKENS

    def __init__(
        self,
        retriever: Optional[QdrantRetriever] = None,
        redis_client: Optional[Any] = None,
        redis_url: str = "redis://localhost:6379/0",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
    ) -> None:
        self.retriever = retriever or QdrantRetriever(collection_name="openclaw_knowledge")
        self.redis_client = redis_client if redis_client is not None else self._build_redis_client(redis_url)
        self.ttl_seconds = int(ttl_seconds)

    def _build_redis_client(self, redis_url: str) -> Optional[Any]:
        if redis is None:
            return None
        try:
            return redis.Redis.from_url(redis_url, decode_responses=True)
        except Exception:
            return None

    def redis_client_connects(self) -> bool:
        """Best-effort connectivity check; false on any Redis failure."""
        try:
            return bool(self.redis_client is not None and self.redis_client.ping())
        except Exception:
            return False

    @staticmethod
    def cache_key(query: str, collection_name: str, top_k: int) -> str:
        """Deterministic cache key including query hash, collection name, and top_k."""
        normalized_query = " ".join((query or "").strip().lower().split())
        query_hash = hashlib.sha256(normalized_query.encode("utf-8")).hexdigest()
        safe_collection = re.sub(r"[^A-Za-z0-9_.:-]", "_", collection_name or "")
        return f"{CACHE_PREFIX}:{safe_collection}:top_k={int(top_k)}:q={query_hash}"

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        return len(text or "") // 4

    @classmethod
    def _has_secret(cls, text: str) -> bool:
        return any(pattern.search(text or "") for pattern in SECRET_PATTERNS)

    def _chunk_is_cache_safe(self, chunk: Dict[str, Any]) -> bool:
        payload = chunk.get("payload", {}) or {}
        if self.retriever._is_forbidden_path(payload):
            return False
        text = str(chunk.get("text", ""))
        if self._has_secret(text) or self._has_secret(json.dumps(payload, default=str)):
            return False
        return True

    def _safe_cache_payload(self, result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if result.get("status") not in {"success", "empty"}:
            return None
        if result.get("status") == "empty":
            return {
                "status": "empty",
                "query": result.get("query", ""),
                "chunks": [],
                "results": [],
                "chunk_count": 0,
                "total_tokens": 0,
                "message": "No relevant knowledge found.",
            }

        safe_chunks = []
        total_tokens = 0
        for chunk in result.get("chunks", [])[: self.max_cached_chunks_per_query]:
            if not self._chunk_is_cache_safe(chunk):
                continue
            text = str(chunk.get("text", ""))
            token_count = self._estimate_tokens(text)
            if total_tokens + token_count > self.max_cached_total_tokens:
                break
            payload = chunk.get("payload", {}) or {}
            safe_chunks.append({
                "text": text,
                "score": chunk.get("score", 0),
                "id": str(chunk.get("id")),
                "payload": {
                    "source_path": payload.get("source_path") or payload.get("path"),
                    "path": payload.get("path") or payload.get("source_path"),
                    "chunk_id": payload.get("chunk_id"),
                    "approved_batch": payload.get("approved_batch"),
                },
            })
            total_tokens += token_count

        if not safe_chunks:
            return {
                "status": "empty",
                "query": result.get("query", ""),
                "chunks": [],
                "results": [],
                "chunk_count": 0,
                "total_tokens": 0,
                "message": "No relevant knowledge found.",
            }

        return {
            "status": "success",
            "query": result.get("query", ""),
            "chunks": safe_chunks,
            "results": safe_chunks,
            "chunk_count": len(safe_chunks),
            "total_tokens": total_tokens,
            "max_chunk_tokens": QdrantRetriever.MAX_CHUNK_TOKENS,
            "max_total_tokens": self.max_cached_total_tokens,
            "cache": "redis",
        }

    def get(self, query: str, collection_name: str, top_k: int) -> Optional[Dict[str, Any]]:
        if self.redis_client is None:
            return None
        try:
            raw = self.redis_client.get(self.cache_key(query, collection_name, top_k))
            if not raw:
                return None
            parsed = json.loads(raw)
            if not isinstance(parsed, dict):
                return None
            return parsed
        except Exception:
            return None

    def set(self, query: str, collection_name: str, top_k: int, result: Dict[str, Any]) -> bool:
        if self.redis_client is None:
            return False
        payload = self._safe_cache_payload(result)
        if payload is None:
            return False
        try:
            key = self.cache_key(query, collection_name, top_k)
            self.redis_client.setex(key, self.ttl_seconds, json.dumps(payload, ensure_ascii=False))
            return True
        except Exception:
            return False

    def retrieve(self, query: str, top_k: int = QdrantRetriever.DEFAULT_TOP_K, semantic_filter: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve with cache. Miss/failure falls back to read-only Qdrant retrieval."""
        if ContextManager.is_at_block_threshold():
            return {
                "status": "skipped",
                "skipped": True,
                "reason": "Retrieval skipped due to context pressure.",
                "results": [],
                "chunks": [],
                "chunk_count": 0,
                "total_tokens": 0,
            }

        effective_top_k = min(max(int(top_k), 0), QdrantRetriever.DEFAULT_TOP_K)
        if ContextManager.is_above_warning_threshold():
            effective_top_k = max(1, effective_top_k // 2)

        collection_name = self.retriever.collection_name
        cached = self.get(query, collection_name, effective_top_k)
        if cached is not None:
            cached["cache_hit"] = True
            return cached

        result = self.retriever.retrieve(query, top_k=effective_top_k, semantic_filter=semantic_filter)
        self.set(query, collection_name, effective_top_k, result)
        result["cache_hit"] = False
        return result
