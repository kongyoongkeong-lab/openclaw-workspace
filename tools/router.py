#!/usr/bin/env python3
"""
OpenClaw Router with Context Pruning
Phase 6 Integration: Dead context removal, LRU cache optimization
"""

from typing import Dict, List, Optional
from collections import OrderedDict
from tools.context_pruner import ContextPruner
from tools.select_tool_stack import select_tool_stack
from tools.tool_mapping import tool_mapping, DEFAULT_FALLBACK_CHAIN

# Initialize context pruner for dead context removal
context_pruner = ContextPruner(max_context_size=2048, max_tokens=8192)


def route_request(query: str, cache: Dict, rpr: float) -> Dict:
    """
    Route incoming request with context pruning optimization.
    - Select tools based on query semantics
    - Apply dead context removal
    - Enforce fallback chain for deterministic behavior
    """
    # Select tool stack
    tool_stack = select_tool_stack(query, cache, rpr, depth_limit=3)
    
    # Prune context
    if "context" in tool_stack:
        optimized_context = context_pruner.prune_context(tool_stack["context"])
        tool_stack["context"] = optimized_context
    
    return tool_stack


def gate_budget(context: Dict) -> Dict:
    """
    Apply governance checks before routing.
    - Enforce max_context_size
    - Remove dead context
    - Optimize for TRI scores
    """
    optimized = context_pruner.optimize(context)
    return optimized


if __name__ == "__main__":
    print("Router initialized with Context Pruning (Phase 6)")
