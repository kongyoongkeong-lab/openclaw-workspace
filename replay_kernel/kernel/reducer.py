"""
Pure Reducer — State Application Layer
Replay Kernel v0 — Deterministic State Machine
"""

import copy
from datetime import datetime, timezone
from typing import Any, Optional

from events.schema import Event, EventType, make_event

class State:
    """Immutable state representation."""
    
    def __init__(self, messages: list[dict] = None, systems: list[dict] = None,
                 tools: list[dict] = None, decisions: list[dict] = None,
                 open_loops: list[str] = None, active_entities: list[str] = None):
        self.messages = messages or []
        self.systems = systems or []
        self.tools = tools or []
        self.decisions = decisions or []
        self.open_loops = open_loops or []
        self.active_entities = active_entities or []
        self.last_update = datetime.now(timezone.utc)
    
    def to_dict(self) -> dict:
        """Convert to dict for logging."""
        return {
            "messages": self.messages,
            "systems": self.systems,
            "tools": self.tools,
            "decisions": self.decisions,
            "open_loops": self.open_loops,
            "active_entities": self.active_entities,
            "last_update": self.last_update.isoformat(),
        }
    
    @classmethod
    def empty(cls) -> "State":
        """Create empty initial state."""
        return cls()
    
    def copy(self) -> "State":
        """Return deep copy for mutation during apply_event."""
        return State(
            messages=copy.deepcopy(self.messages),
            systems=copy.deepcopy(self.systems),
            tools=copy.deepcopy(self.tools),
            decisions=copy.deepcopy(self.decisions),
            open_loops=copy.deepcopy(self.open_loops),
            active_entities=copy.deepcopy(self.active_entities),
        )

def apply_event(state: State, event: Event) -> State:
    """
    Pure reducer: apply event to state (immutable transformation).
    
    This is the heart of deterministic replay:
    - No summarization
    - No compression
    - No state mutation outside the function
    
    Args:
        state: Current immutable state
        event: Event to apply
    
    Returns:
        New state (deep copy mutated, then returned)
    """
    new_state = state.copy()
    
    if event.event_type == EventType.USER_MESSAGE:
        new_state.messages.append(event.payload)
    
    elif event.event_type == EventType.SYSTEM:
        new_state.systems.append(event.payload)
    
    elif event.event_type == EventType.TOOL:
        new_state.tools.append(event.payload)
    
    elif event.event_type == EventType.AGENT_TURN:
        new_state.decisions.append(event.payload)
    
    elif event.event_type == EventType.DIVERGENCE:
        new_state.systems.append({
            "type": "divergence_check",
            **event.payload,
        })
    
    new_state.last_update = event.timestamp
    
    return new_state

def apply_event_batch(state: State, events: list[Event]) -> State:
    """Apply multiple events in order (deterministic replay)."""
    result = state
    for event in events:
        result = apply_event(result, event)
    return result
