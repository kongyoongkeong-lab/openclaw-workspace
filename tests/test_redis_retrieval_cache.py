#!/usr/bin/env python3
"""Tests for Redis Retrieval Cache v0."""

import json
import os
import sys
from unittest.mock import Mock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runtime.cache.redis_retrieval_cache import (  # noqa: E402
    DEFAULT_TTL_SECONDS,
    RedisRetrievalCache,
)
from runtime.render.render_policy import RenderPolicy  # noqa: E402


class FakeRedis:
    def __init__(self, fail_get=False, fail_set=False):
        self.store = {}
        self.ttls = {}
        self.fail_get = fail_get
        self.fail_set = fail_set

    def ping(self):
        return True

    def get(self, key):
        if self.fail_get:
            raise RuntimeError("redis get failed")
        return self.store.get(key)

    def setex(self, key, ttl, value):
        if self.fail_set:
            raise RuntimeError("redis set failed")
        self.store[key] = value
        self.ttls[key] = ttl
        return True


def make_retriever(result=None):
    retriever = Mock()
    retriever.collection_name = "openclaw_knowledge"
    retriever._is_forbidden_path.side_effect = lambda payload: "logs/" in str(payload).lower() or ".env" in str(payload).lower()
    retriever.retrieve.return_value = result or {
        "status": "success",
        "query": "current OpenClaw phase",
        "chunks": [
            {
                "text": "Phase H1 strict validation.",
                "score": 0.9,
                "id": "p1",
                "payload": {"source_path": "memory/state_summary.md", "path": "memory/state_summary.md", "chunk_id": 0, "approved_batch": "low-risk-v0"},
            }
        ],
        "results": [],
        "chunk_count": 1,
        "total_tokens": 6,
    }
    return retriever


def test_redis_client_connects():
    cache = RedisRetrievalCache(retriever=make_retriever(), redis_client=FakeRedis())
    assert cache.redis_client_connects() is True


def test_cache_key_deterministic():
    key1 = RedisRetrievalCache.cache_key(" Current  OpenClaw Phase ", "openclaw_knowledge", 5)
    key2 = RedisRetrievalCache.cache_key("current openclaw phase", "openclaw_knowledge", 5)
    key3 = RedisRetrievalCache.cache_key("current openclaw phase", "openclaw_knowledge", 3)
    assert key1 == key2
    assert key1 != key3
    assert "openclaw_knowledge" in key1
    assert "top_k=5" in key1


def test_cache_miss_falls_back_to_qdrant():
    redis_client = FakeRedis()
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)

    result = cache.retrieve("current OpenClaw phase")

    retriever.retrieve.assert_called_once()
    assert result["cache_hit"] is False
    assert result["status"] == "success"


def test_cache_hit_skips_qdrant():
    redis_client = FakeRedis()
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)
    key = cache.cache_key("current OpenClaw phase", "openclaw_knowledge", 5)
    redis_client.store[key] = json.dumps({
        "status": "success",
        "query": "current OpenClaw phase",
        "chunks": [{"text": "cached", "payload": {"source_path": "memory/state_summary.md"}}],
        "results": [{"text": "cached", "payload": {"source_path": "memory/state_summary.md"}}],
        "chunk_count": 1,
        "total_tokens": 1,
    })

    result = cache.retrieve("current OpenClaw phase")

    retriever.retrieve.assert_not_called()
    assert result["cache_hit"] is True
    assert result["chunks"][0]["text"] == "cached"


def test_ttl_applied():
    redis_client = FakeRedis()
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)

    cache.retrieve("current OpenClaw phase")

    assert list(redis_client.ttls.values()) == [DEFAULT_TTL_SECONDS]


def test_forbidden_paths_not_cached():
    redis_client = FakeRedis()
    retriever = make_retriever({
        "status": "success",
        "query": "unsafe",
        "chunks": [
            {"text": "raw log", "payload": {"source_path": "logs/session.log", "path": "logs/session.log"}}
        ],
        "chunk_count": 1,
        "total_tokens": 2,
    })
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)

    result = cache.retrieve("unsafe")

    assert result["cache_hit"] is False
    cached = list(redis_client.store.values())[0]
    assert "logs/session.log" not in cached
    assert json.loads(cached)["status"] == "empty"


def test_secrets_not_cached():
    redis_client = FakeRedis()
    retriever = make_retriever({
        "status": "success",
        "query": "secret",
        "chunks": [
            {"text": "api_key = abc123", "payload": {"source_path": "memory/state_summary.md", "path": "memory/state_summary.md"}}
        ],
        "chunk_count": 1,
        "total_tokens": 4,
    })
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)

    cache.retrieve("secret")

    cached = list(redis_client.store.values())[0]
    assert "api_key" not in cached
    assert json.loads(cached)["status"] == "empty"


def test_redis_failure_degrades_gracefully():
    redis_client = FakeRedis(fail_get=True, fail_set=True)
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)

    result = cache.retrieve("current OpenClaw phase")

    retriever.retrieve.assert_called_once()
    assert result["status"] == "success"
    assert result["cache_hit"] is False


def test_progress_returns_exactly():
    assert RenderPolicy.route_render("progress", "") == "Stable. No user action required."


def test_context_block_skips_retrieval_and_cache():
    redis_client = FakeRedis()
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)
    with patch("runtime.cache.redis_retrieval_cache.ContextManager.is_at_block_threshold", return_value=True):
        result = cache.retrieve("current OpenClaw phase")
    retriever.retrieve.assert_not_called()
    assert result["status"] == "skipped"
    assert result["reason"] == "Retrieval skipped due to context pressure."


def test_warning_pressure_reduces_top_k():
    redis_client = FakeRedis()
    retriever = make_retriever()
    cache = RedisRetrievalCache(retriever=retriever, redis_client=redis_client)
    with patch("runtime.cache.redis_retrieval_cache.ContextManager.is_at_block_threshold", return_value=False):
        with patch("runtime.cache.redis_retrieval_cache.ContextManager.is_above_warning_threshold", return_value=True):
            cache.retrieve("current OpenClaw phase", top_k=5)
    assert retriever.retrieve.call_args.kwargs["top_k"] == 2
