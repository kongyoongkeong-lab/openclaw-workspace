#!/usr/bin/env python3
"""Manual RAG Query Mode v0.

Explicit-only retrieval command:
    rag query <question>

No automatic retrieval, no writes, no memory learning, no cache, no tool/agent registration.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
RAG_PATH = ROOT / "runtime" / "rag"
if str(RAG_PATH) not in sys.path:
    sys.path.insert(0, str(RAG_PATH))

from qdrant_retriever import QdrantRetriever  # noqa: E402

COMMAND_PREFIX = "rag query "
SKIPPED_MESSAGE = "Retrieval skipped due to context pressure."
EMPTY_MESSAGE = "No relevant knowledge found."


def is_manual_rag_query(command: str) -> bool:
    """Return True only for the explicit manual RAG command."""
    return bool(command and command.strip().lower().startswith(COMMAND_PREFIX))


def extract_question(command: str) -> Optional[str]:
    """Extract the question from `rag query <question>`."""
    if not is_manual_rag_query(command):
        return None
    question = command.strip()[len(COMMAND_PREFIX):].strip()
    return question or None


def _clean_snippet(text: str, limit: int = 220) -> str:
    """Create a deterministic concise snippet from retrieved chunk text."""
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def format_retrieval_answer(result: dict) -> str:
    """Format retrieval results concisely with source paths."""
    status = result.get("status")
    if status == "skipped":
        return SKIPPED_MESSAGE
    if status in {"empty", "error"} or not result.get("chunks"):
        return EMPTY_MESSAGE if status != "error" else "Retrieval failed."

    lines = ["Relevant knowledge found:"]
    seen_sources = set()
    for chunk in result.get("chunks", []):
        payload = chunk.get("payload", {}) or {}
        source = payload.get("source_path") or payload.get("path") or "unknown"
        snippet = _clean_snippet(chunk.get("text", ""))
        key = (source, snippet)
        if key in seen_sources:
            continue
        seen_sources.add(key)
        lines.append(f"- {source}: {snippet}")
        if len(lines) >= 6:  # header + top 5 chunks
            break

    return "\n".join(lines) if len(lines) > 1 else EMPTY_MESSAGE


def handle_manual_rag_query(command: str, retriever: Optional[QdrantRetriever] = None) -> Optional[str]:
    """
    Handle `rag query <question>` only.

    Returns None for all non-manual-RAG commands so normal prompts never trigger retrieval.
    """
    question = extract_question(command)
    if question is None:
        return None

    retriever = retriever or QdrantRetriever(collection_name="openclaw_knowledge")
    result = retriever.retrieve(
        question,
        top_k=QdrantRetriever.DEFAULT_TOP_K,
        semantic_filter=None,
    )
    return format_retrieval_answer(result)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Manual explicit-only Qdrant RAG query v0")
    parser.add_argument("command", nargs="*", help="Command text, e.g. rag query current OpenClaw phase")
    args = parser.parse_args(argv)

    command = " ".join(args.command).strip()
    output = handle_manual_rag_query(command)
    if output is None:
        print("No manual RAG query requested.")
        return 2
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
