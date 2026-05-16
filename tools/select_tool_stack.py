"""
select_tool_stack.py - Complexity-Based Tool Selection
Deterministic, H1-compliant, RPR-aware
"""

import json
from typing import List, Dict, Any

# Load Tool Mapping and TRI scores
def load_tool_mapping() -> Dict:
    with open("/home/jason2ykk/.openclaw/workspace/tools/tool_mapping.json") as f:
        return json.load(f)

# Task Complexity Estimator
def estimate_task_complexity(task: str, context: Dict) -> int:
    """Estimate task complexity: <3 simple, =3 medium, >3 high"""
    keywords = {
        "simple": ["read", "fetch", "search", "status", "list"],
        "medium": ["analysis", "browser", "edit", "write", "message"],
        "high": ["complex", "multi-", "full-", "deep-", "generate", "orchestrate"],
    }
    task_lower = task.lower()
    simple_count = sum(1 for k in keywords["simple"] if k in task_lower)
    medium_count = sum(1 for k in keywords["medium"] if k in task_lower)
    high_count = sum(1 for k in keywords["high"] if k in task_lower)
    
    if high_count > simple_count + medium_count:
        return 4  # High
    elif medium_count >= simple_count:
        return 3  # Medium
    else:
        return 1  # Simple

# Tool Inertia Cache
def get_tool_inertia(task_type: str, next_tool: str, cache: Dict) -> float:
    """Get transition probability from inertia cache"""
    return cache.get(task_type, {}).get(next_tool, 0.0)

# Context-Based Tool Filtering
def filter_tools_by_context(task_intent: str, recent_outputs: List[Dict], RPR: float) -> List[str]:
    """Restrict to high-value TRI tools if RPR > 0.09"""
    high_value_tools = [
        "web_search", "tavily_search",
        "memory_search", "memory_get",
        "file_fetch", "read", "pdf",
    ]
    return high_value_tools if RPR > 0.09 else None

# Select Tool Stack
def select_tool_stack(task: str, context: Dict, cache: Dict = {}, RPR: float = 0.0) -> Dict:
    """
    Returns: {
        "ordered_stack": [tool1, tool2, ...],
        "execution_budget_ms": int,
        "risk_tier": str,
        "selection_method": str,
    }
    """
    tool_mapping = load_tool_mapping()
    complexity = estimate_task_complexity(task, context)
    
    # Fallback chains for complexity levels
    DEFAULT_FALLBACK_CHAIN = [
        "web_search", "memory_search", "browser",
        "tavily_search", "file_fetch", "tavily_extract"
    ]
    
    # Step 2: Complexity-based dispatch
    if complexity < 3:  # Simple
        tool_stack = DEFAULT_FALLBACK_CHAIN
        method = "direct_match"
    elif complexity == 3:  # Medium
        tool_stack = DEFAULT_FALLBACK_CHAIN
        method = "parallel_to_serial"
    else:  # High
        tool_stack = DEFAULT_FALLBACK_CHAIN
        method = "specialized_chain"
    
    # Step 3: RPR filtering
    if RPR > 0.09:
        filtered_tools = filter_tools_by_context(task, [], RPR)
        if filtered_tools:
            tool_stack = [t for t in tool_stack if t in filtered_tools]
            method = f"{method} + RPR_filter"
    
    # Step 4: TRI score ordering
    ordered_stack = sorted(tool_stack, key=lambda t: tool_mapping.get(t, {}).get("tri", 0), reverse=True)
    
    return {
        "ordered_stack": ordered_stack,
        "execution_budget_ms": 1000 if complexity < 3 else 3000 if complexity == 3 else 5000,
        "risk_tier": "low" if complexity < 3 else "medium" if complexity == 3 else "high",
        "selection_method": method,
    }

# Main entry point
if __name__ == "__main__":
    task = "web_fetch https://docs.openclaw.ai"
    context = {"RPR": 0.09, "cache": {}, "last_used": None}
    result = select_tool_stack(task, context, {})
    print(json.dumps(result, indent=2))
