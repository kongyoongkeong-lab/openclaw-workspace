#!/usr/bin/env python3
"""Curated LOW-risk ingest for openclaw_knowledge.

Approved batch only. No global RAG enablement, no Redis, no tool registration.
"""

from pathlib import Path
import re
import sys
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

ROOT = Path(__file__).resolve().parents[1]
RAG_PATH = ROOT / "runtime" / "rag"
sys.path.insert(0, str(RAG_PATH))
from qdrant_retriever import QdrantRetriever  # noqa: E402

COLLECTION = "openclaw_knowledge"
APPROVED = [
    "memory/state_summary.md",
    "docs/protocols/github_integration_protocol.md",
    "security/github_usage_policy.md",
    "docs/reports/h1_quiet_soak_result.md",
]
FORBIDDEN_PATH_PARTS = [
    ".env", "logs/", "traces/", "storage/", "qdrant/", "redis/",
    "models/", ".jsonl", "browser", "cookies",
]
CREDENTIAL_PATTERNS = [
    re.compile(r"https://discord(?:app)?\.com/api/webhooks/", re.I),
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"),
    re.compile(r"(?i)(api[_\s-]?key|secret|token|password)\s*[:=]\s*['\"]?\S+"),
]
MAX_CHUNK_TOKENS = 800
MAX_CHARS = MAX_CHUNK_TOKENS * 4


def forbidden_path(path: str) -> bool:
    lowered = path.lower()
    return any(part in lowered for part in FORBIDDEN_PATH_PARTS)


def has_credential_like_content(text: str) -> bool:
    return any(pattern.search(text) for pattern in CREDENTIAL_PATTERNS)


def chunks_for(text: str) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= MAX_CHARS:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(paragraph) <= MAX_CHARS:
                current = paragraph
            else:
                for start in range(0, len(paragraph), MAX_CHARS):
                    chunks.append(paragraph[start:start + MAX_CHARS])
                current = ""
    if current:
        chunks.append(current)
    return chunks


def point_id(source_path: str, chunk_id: int) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"openclaw-rag-v0:{source_path}:{chunk_id}"))


def main() -> int:
    client = QdrantClient(url="http://localhost:6333")
    names = [collection.name for collection in client.get_collections().collections]
    if COLLECTION not in names:
        print("openclaw_knowledge collection missing. User approval required to create.")
        return 2

    points = []
    for source_path in APPROVED:
        if forbidden_path(source_path):
            print(f"blocked forbidden path: {source_path}")
            return 3
        file_path = ROOT / source_path
        if not file_path.is_file():
            print(f"approved file missing: {source_path}")
            return 4
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        if has_credential_like_content(text):
            print(f"credential-like pattern detected; skipped batch: {source_path}")
            return 5
        for idx, chunk in enumerate(chunks_for(text)):
            payload = {
                "source_path": source_path,
                "path": source_path,
                "chunk_id": idx,
                "text": chunk,
                "approved_batch": "low-risk-v0",
            }
            if has_credential_like_content(chunk):
                print(f"blocked unsafe chunk: {source_path}#{idx}")
                return 6
            points.append(PointStruct(
                id=point_id(source_path, idx),
                vector=QdrantRetriever._text_vector(chunk),
                payload=payload,
            ))

    if points:
        client.upsert(collection_name=COLLECTION, points=points, wait=True)
    print(f"ingested_points={len(points)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
