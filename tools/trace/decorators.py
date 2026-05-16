#!/usr/bin/env python3
"""
Trace Tool Wrappers
Production-grade decorators for automatic instrumentation
"""

import asyncio
import time
from functools import wraps
from typing import Callable, Any

from .event_store import append_event

TRACE_EVENTS = [
    "TRIGGER_MATCHED",
    "TOOL_STARTED",
    "TOOL_COMPLETED",
    "TOOL_FAILED",
    "AGENT_HANDOFF",
    "CONTEXT_COMPRESSED",
    "WORKFLOW_COMPLETED",
]

def trace_tool_call(tool_name: str = None):
    """
    Decorator for tool functions - automatic instrumentation
    Usage: @trace_tool_call("browser")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Inject trace_id from outer scope if available
            trace_id = getattr(wrapper, '_current_trace_id', f"t{int(time.time() * 1000)}")
            
            # Record start
            start = time.perf_counter()
            
            try:
                result = await func(*args, **kwargs)
                
                # Record completion
                event = {
                    "trace_id": trace_id,
                    "event": "TOOL_COMPLETED",
                    "ts": time.time(),
                    "tool": func.__name__ if tool_name is None else tool_name,
                    "duration": time.perf_counter() - start,
                    "success": True
                }
                append_event(event)
                
                return result
                
            except Exception as e:
                # Record failure
                event = {
                    "trace_id": trace_id,
                    "event": "TOOL_FAILED",
                    "ts": time.time(),
                    "tool": func.__name__ if tool_name is None else tool_name,
                    "error": str(e),
                    "duration": time.perf_counter() - start
                }
                append_event(event)
                raise
                
        # Attach trace_id to wrapper for chain instrumentation
        return wrapper
    return decorator

def trace_handoff(from_agent: str, to_agent: str):
    """
    Decorator for agent handoffs
    Records context metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            trace_id = getattr(wrapper, '_current_trace_id', f"t{int(time.time() * 1000)}")
            
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            
            event = {
                "trace_id": trace_id,
                "event": "AGENT_HANDOFF",
                "ts": time.time(),
                "from_agent": from_agent,
                "to_agent": to_agent,
                "duration": time.perf_counter() - start
            }
            
            # Optional: record context metrics if available
            if hasattr(wrapper, '_context_tokens'):
                event["context_tokens"] = wrapper._context_tokens
                event["summary_ratio"] = getattr(wrapper, '_summary_ratio', 0.5)
            
            append_event(event)
            return result
        return wrapper
    return decorator

# Context compression helper
def with_context_compression(before_tokens: int, after_tokens: int):
    """Context compression event recorder"""
    event = {
        "event": "CONTEXT_COMPRESSED",
        "before_tokens": before_tokens,
        "after_tokens": after_tokens,
        "compression_ratio": after_tokens / before_tokens if before_tokens else 0,
        "ts": time.time()
    }
    append_event(event)
    return event

if __name__ == "__main__":
    import inspect
    print("Trace decorators loaded successfully")
    print(f"Available event types: {TRACE_EVENTS}")
