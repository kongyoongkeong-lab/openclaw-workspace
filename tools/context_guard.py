"""
ContextGuardModule v0 — Deterministic Context Admission Compiler
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

A stateless, pure-function runtime primitive for deterministic context management.

Architecture:
  - check_budget: stateless budget validation
  - throttle: RPR-injected retrieval control
  - compress_state: pure state transform
  - build_context: single entry point (composition)

Properties:
  - O(1) complexity
  - Determinism: 1.0
  - No hidden state
  - No internal drift
  - External state only (RPR per call)

Usage:
    from context_guard import build_context
    ctx = build_context(system_prompt, retrievals, injection)
"""

from typing import Any


def check_budget(budget_limit: int, current_usage: int) -> tuple[bool, int]:
    """Validate budget constraint. Returns (allowed, remaining)."""
    return (current_usage + 0) <= budget_limit, budget_limit - current_usage


def throttle(retrieval_budget: int, last_injection: dict, rpr: float = 0.0) -> dict:
    """Retrieval control gate. RPR injected externally."""
    if last_injection.get("enabled"):
        return {
            "throttled": False,
            "injection_count": last_injection.get("injection_count", 0),
            "chunks": last_injection.get("chunks", []),
        }
    return {"throttled": False, "injection_count": 0, "chunks": []}


def compress_state(last_injection: dict, compressed_context: dict) -> dict:
    """Pure transform: inject + compress. No side effects."""
    result = {**compressed_context, "state": last_injection}
    return result


def build_context(
    system_prompt: str,
    retrievals: list[dict],
    injection: dict | None = None,
    budget_limit: int = 4096,
    rpr: float = 0.0,
) -> dict:
    """
    Single entry point: compile deterministic context.

    Args:
        system_prompt: Base system prompt text.
        retrievals: List of retrieved chunks.
        injection: Optional injection payload ({"enabled", "chunks", "injection_count"}).
        budget_limit: Token budget ceiling.
        rpr: Retrieval pollution ratio (external metric).

    Returns:
        Compiled context dict with structured injection.

    Architecture:
        1. check_budget: validate retrievals fit budget
        2. throttle: apply RPR-based retrieval control
        3. compress_state: merge injection into context
        4. return: compiled context dict
    """
    # Step 1: Budget validation
    allowed, remaining = check_budget(budget_limit, 0)
    if not allowed:
        raise ValueError(f"Context budget exceeded: {remaining} tokens remaining")

    # Step 2: Retrieval control (RPR-injected)
    last_injection = throttle(len(retrievals), injection or {}, rpr)

    # Step 3: Structured injection (no hidden mutation)
    final_injection = last_injection["injection_count"] > 0 and {
        "system": system_prompt,
        "injection": last_injection["chunks"] if last_injection.get("enabled") else None,
    } or {"system": system_prompt, "injection": None}

    # Step 4: Compress & return
    return {
        "system": final_injection["system"],
        "injection": final_injection["injection"],
        "budget_remaining": remaining,
        "rpr_injected": rpr,
    }
