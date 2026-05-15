#!/usr/bin/env python3
"""Context Guard adapter for Context Manager v1.

Validates context before inference and returns a decision object.
Does not call models except through an explicit guarded callback supplied by tests/runtime.
No RAG ingest, no Redis, no autonomous governance, no telemetry rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Any
import logging
import os
import re

try:
    from .context_budget import estimate_tokens, reserve_output_buffer, get_context_policy
    from .context_planner import ContextPlanner
except ImportError:  # support direct sys.path imports used by local tests
    from context_budget import estimate_tokens, reserve_output_buffer, get_context_policy
    from context_planner import ContextPlanner

LOG_DIR = "/home/jason2ykk/.openclaw/workspace/runtime/logs"
os.makedirs(LOG_DIR, exist_ok=True)
logger = logging.getLogger("context_guard")
logger.setLevel(logging.INFO)
if not logger.handlers:
    from logging.handlers import RotatingFileHandler

    fh = RotatingFileHandler(
        os.path.join(LOG_DIR, "context_budget.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
    logger.addHandler(fh)


@dataclass(frozen=True)
class ContextDecision:
    allowed: bool
    message: str
    tokens_used: int
    output_reserve_tokens: int
    summary_loaded: bool
    final_context: str


def _sanitize_summary(summary: str) -> str:
    """Remove forbidden material from on-demand state summary."""
    if not summary:
        return ""

    blocked_tokens = ("NO_REPLY", "INTERNAL_ONLY", "CONTROL_ONLY", "SYSTEM_ONLY")
    secret_patterns = (
        r"gh[pousr]_[A-Za-z0-9_]{20,}",
        r"(?i)authorization\s*:\s*bearer\s+\S+",
        r"(?i)(api[_ -]?key|password|secret|token)\s*[:=]\s*\S+",
        r"https://discord(?:app)?\.com/api/webhooks/\S+",
    )
    raw_telemetry_patterns = (r"\{\s*\"", r"trace_id", r"jsonl", r"raw telemetry")

    cleaned_lines = []
    for line in summary.splitlines():
        if any(token in line for token in blocked_tokens):
            continue
        if any(re.search(pattern, line) for pattern in secret_patterns):
            continue
        if any(re.search(pattern, line, re.IGNORECASE) for pattern in raw_telemetry_patterns):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines).strip()


def validate_context(
    prompt: str,
    system: Optional[str] = None,
    messages: Optional[list] = None,
    *,
    context_limit: int = 8192,
    heavy_mode: bool = False,
    task_complexity: Optional[str] = None,
) -> ContextDecision:
    """Run context budget + planner checks before inference."""
    planner = ContextPlanner(context_limit=context_limit, heavy_mode=heavy_mode)
    allowed, message = planner.plan(prompt=prompt, system=system, messages=messages)
    tokens_used = planner.used_tokens
    output_reserve = reserve_output_buffer(context_limit)

    if not allowed:
        logger.warning(
            "Context blocked before inference: used=%s limit=%s reason=%s",
            tokens_used,
            context_limit,
            message,
        )
        return ContextDecision(False, message, tokens_used, output_reserve, False, "")

    policy = get_context_policy()
    pressure = tokens_used >= policy["warning_threshold_tokens"]
    complex_task = heavy_mode or (task_complexity or "").lower() in {"complex", "high"}
    summary_loaded = False
    final_context = prompt

    if pressure or complex_task:
        summary = _sanitize_summary(planner.load_summary_on_demand() or "")
        if summary:
            final_context = f"{summary}\n\n---\n\n{prompt}"
            summary_loaded = True
            logger.info("Context summary loaded on-demand: used=%s", tokens_used)

    if pressure:
        logger.warning("Context warning before inference: used=%s limit=%s", tokens_used, context_limit)

    return ContextDecision(True, message, tokens_used, output_reserve, summary_loaded, final_context)


def guarded_model_call(model_call: Callable[[str], Any], prompt: str, **kwargs: Any) -> Any:
    """Validate context before invoking an explicit model callback."""
    decision = validate_context(prompt, **kwargs)
    if not decision.allowed:
        raise RuntimeError(decision.message)
    return model_call(decision.final_context)
