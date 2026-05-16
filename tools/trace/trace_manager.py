#!/usr/bin/env python3
"""
Trace Manager - Workflow Lifecycle Orchestration
"""

import time
from typing import List, Dict, Optional
from datetime import datetime

from .event_store import append_event, get_events_by_trace_id
from .decorators import trace_tool_call, trace_handoff
from .resource_snapshot import take_resource_snapshot, trace_phase_boundary

class TraceManager:
    """Manages trace lifecycle for daily_news workflow"""
    
    def __init__(self, workflow_name: str = "daily_news"):
        self.workflow_name = workflow_name
        self._current_trace_id = f"daily_{int(time.time() * 1000)}"
        self._set_trace_id()
    
    def _set_trace_id(self):
        """Attach trace_id to self for decorator access"""
        self._current_trace_id = f"daily_{int(time.time() * 1000)}"
    
    def start(self) -> str:
        """Initiate trace capture"""
        append_event({
            "trace_id": self._current_trace_id,
            "event": "WORKFLOW_INIT",
            "ts": time.time(),
            "workflow": self.workflow_name,
            "snapshot": take_resource_snapshot()
        })
        
        print(f"[TRACE] {self._current_trace_id} - Workflow {self.workflow_name} initialized")
        print(f"[TRACE] Event stream: /home/jason2ykk/.openclaw/workspace/traces/2026-05-14.jsonl")
        return self._current_trace_id
    
    def phase_transition(self, phase: str) -> dict:
        """Record phase boundary"""
        return trace_phase_boundary(phase.upper())
    
    def tool_call(self, tool_name: str, *args, **kwargs):
        """Execute tool with automatic tracing"""
        def traced_func(*args, **kwargs):
            result = None
            try:
                result = tool_name(*args, **kwargs)
            except Exception as e:
                raise e
            return result
        
        # Attach trace_id for decorator chain
        traced_func._current_trace_id = self._current_trace_id
        
        # Use decorator wrapper for this call
        @trace_tool_call(tool_name)
        async def async_wrapper(*args, **kwargs):
            return await traced_func(*args, **kwargs)
        
        return async_wrapper(*args, **kwargs)
    
    def agent_handoff(self, from_agent: str, to_agent: str) -> dict:
        """Record agent handoff with context metrics"""
        # For testing, mock context metrics
        handoff_event = {
            "trace_id": self._current_trace_id,
            "event": "AGENT_HANDOFF",
            "ts": time.time(),
            "from_agent": from_agent,
            "to_agent": to_agent,
            "duration": 0.001
        }
        
        # Optional context metrics (mock for demo)
        handoff_event["context_tokens"] = len(self._get_active_context())
        handoff_event["summary_ratio"] = 0.62
        
        append_event(handoff_event)
        return handoff_event
    
    def _get_active_context(self) -> List[str]:
        """Get active context tokens (mock for demo)"""
        return ["context_item_1", "context_item_2"]
    
    def complete(self) -> dict:
        """Mark workflow completion"""
        event = {
            "trace_id": self._current_trace_id,
            "event": "WORKFLOW_COMPLETED",
            "ts": time.time(),
            "workflow": self.workflow_name,
            "total_events": len(get_events_by_trace_id(self._current_trace_id))
        }
        
        append_event(event)
        return event
    
    def get_trace(self) -> Dict:
        """Get full trace"""
        return {
            "trace_id": self._current_trace_id,
            "workflow": self.workflow_name,
            "events": get_events_by_trace_id(self._current_trace_id),
            "status": "completed"
        }

# Convenience function
def workflow_trace(workflow_name: str, *args, **kwargs):
    """
    Create trace manager for workflow
    Usage: tm = workflow_trace("daily_news")
    """
    return TraceManager(workflow_name)

if __name__ == "__main__":
    # Test trace manager
    tm = TraceManager("daily_news")
    trace_id = tm.start()
    print(f"Trace ID: {trace_id}")
    print(f"Events recorded: {tm.get_trace()['events']}")
