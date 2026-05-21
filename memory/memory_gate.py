#!/usr/bin/env python3
"""
Memory Gate Layer - v1
Core firewall: enforces hard token budget BEFORE LLM call
"""

import re


def estimate_tokens(text):
    """Estimate token count using simple heuristic"""
    if not text:
        return 0
    # Average token size: ~4 chars per token
    return len(str(text)) // 4


def memory_gate(entries, max_tokens=8000, query_type="semantic"):
    """
    HARD BUDGET ENFORCER  
    
    Budget by Type:
    - Semantic: k=5 (facts)
    - Episodic: k=3 (events)
    - Governance: k=2 (state)
    - Active task: k=5 (history)
    - Diagnostics: k=1 (summary)
    
    CRITICAL: This is the firewall that prevents overflow.
    """
    selected = []
    tokens = 0

    for e in entries:
        text = e.get("text", "")
        t = estimate_tokens(text)

        # CRITICAL CHECK: would this exceed budget?
        if tokens + t > max_tokens:
            break

        selected.append(e)
        tokens += t

    # Apply retrieval budget based on type (override k after gate)
    # This is a soft cap on entries, NOT tokens
    budget_map = {
        "semantic": 5,
        "episodic": 3,
        "governance": 2,
        "diagnostics": 1,
        "active": 5,
    }
    
    limit = budget_map.get(query_type, 3)  # Default to episodic (3)
    return selected[:limit]


if __name__ == "__main__":
    # Test gate
    test_entries = [
        {"text": "Brief one-liner", "timestamp": "2026-05-06"},
        {"text": "This is a moderately long text entry that uses more tokens.", "timestamp": "2026-05-06"},
        {"text": "Another very long entry that would consume significant token budget and might cause issues if we don't gate properly.", "timestamp": "2026-05-06"},
    ]
    result = memory_gate(test_entries, max_tokens=200)
    print(f"Selected {len(result)} entries (budget: 200 tokens):")
    for e in result:
        print(f"  {e['timestamp']}: {len(e['text'])} chars")
