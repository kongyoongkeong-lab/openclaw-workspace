#!/usr/bin/env python3
"""
OpenClaw Router - Tool Selection & Budget Enforcement
Phase 5 Live | Determinism: 1.0 | RPR: 0.09
"""

import json
import os
import sys
from typing import Optional

# Tool heuristics module
try:
    from tools.select_tool_stack import select_tool_stack
    from tools.tool_mapping import tool_mapping
    HEURISTICS_ENABLED = True
except ImportError:
    HEURISTICS_ENABLED = False

# Budget & depth gates
MAX_DEPTH = 3
TOOL_BUDGET = 100

def gate_budget(tool_stack: list, task: str) -> tuple[bool, str]:
    """Check if task/tool stack obeys budget constraints."""
    if not HEURISTICS_ENABLED:
        return True, "Bypass: heuristics disabled"
    
    used = sum(t.get("used_cost", 0) for t in tool_stack)
    if used >= TOOL_BUDGET:
        return False, f"Budget exceeded: {used}/{TOOL_BUDGET}"
    return True, "OK"

def route_request(task: str, context: Optional[dict] = None) -> list:
    """Select tool stack via heuristics with fallback."""
    if not HEURISTICS_ENABLED:
        return ["web_search"]  # Default fallback
    
    # Enforce depth
    stack = select_tool_stack(task, context)
    if len(stack) > MAX_DEPTH:
        stack = stack[:MAX_DEPTH]
    
    # Budget gate
    ok, msg = gate_budget(stack, task)
    if not ok:
        stack = []  # Deny
    
    return stack

if __name__ == "__main__":
    demo_task = "analyze PDF report"
    tools = route_request(demo_task)
    print(f"Selected tools for '{demo_task}': {tools}")
