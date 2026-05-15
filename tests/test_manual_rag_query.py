#!/usr/bin/env python3
"""Regression tests for Manual RAG Query Mode v0."""

import os
import sys
from unittest.mock import Mock, patch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runtime.rag.manual_query import (  # noqa: E402
    EMPTY_MESSAGE,
    SKIPPED_MESSAGE,
    extract_question,
    handle_manual_rag_query,
    is_manual_rag_query,
)
from runtime.render.render_policy import RenderPolicy  # noqa: E402


def test_only_explicit_rag_query_triggers_retrieval():
    assert is_manual_rag_query("rag query current OpenClaw phase") is True
    assert is_manual_rag_query("RAG QUERY current OpenClaw phase") is True
    assert is_manual_rag_query("current OpenClaw phase") is False
    assert is_manual_rag_query("query current OpenClaw phase") is False
    assert is_manual_rag_query("rag current OpenClaw phase") is False


def test_extract_question():
    assert extract_question("rag query current OpenClaw phase") == "current OpenClaw phase"
    assert extract_question("rag query   ") is None
    assert extract_question("normal prompt") is None


def test_normal_prompt_does_not_retrieve():
    retriever = Mock()
    output = handle_manual_rag_query("How do I verify GitHub CI?", retriever=retriever)
    assert output is None
    retriever.retrieve.assert_not_called()


def test_manual_query_uses_defaults_and_formats_sources():
    retriever = Mock()
    retriever.retrieve.return_value = {
        "status": "success",
        "chunks": [
            {
                "text": "Current OpenClaw phase is H1 strict validation.",
                "payload": {"source_path": "memory/state_summary.md"},
            }
        ],
    }

    output = handle_manual_rag_query("rag query current OpenClaw phase", retriever=retriever)

    retriever.retrieve.assert_called_once_with(
        "current OpenClaw phase",
        top_k=5,
        semantic_filter=None,
    )
    assert "Relevant knowledge found:" in output
    assert "memory/state_summary.md" in output
    assert "Current OpenClaw phase" in output


def test_empty_result_returns_exact_message():
    retriever = Mock()
    retriever.retrieve.return_value = {"status": "empty", "chunks": []}

    assert handle_manual_rag_query("rag query unrelated random topic", retriever=retriever) == EMPTY_MESSAGE


def test_context_block_skip_returns_exact_message():
    retriever = Mock()
    retriever.retrieve.return_value = {"status": "skipped", "reason": SKIPPED_MESSAGE, "chunks": []}

    assert handle_manual_rag_query("rag query current OpenClaw phase", retriever=retriever) == SKIPPED_MESSAGE


def test_progress_still_locked():
    assert RenderPolicy.route_render("progress", "") == "Stable. No user action required."


def test_no_qdrant_write_methods_called_for_manual_query():
    retriever = Mock()
    retriever.retrieve.return_value = {"status": "empty", "chunks": []}

    handle_manual_rag_query("rag query current OpenClaw phase", retriever=retriever)

    for method_name in ["upsert", "delete", "set_payload", "upload_points", "delete_collection"]:
        getattr(retriever, method_name).assert_not_called()
