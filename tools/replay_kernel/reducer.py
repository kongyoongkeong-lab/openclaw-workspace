"""
Replay Kernel v0 - Pure Reducer Layer
==================================================
Core principle:
  reducer MUST be pure
  
  new_state = apply_event(old_state, event)
  
Forbidden operations:
  - file writes
  - logging
  - network calls (Redis/Qdrant)
  - external retrieval
  - mutation of input state
"""

from typing import Any, Dict, Optional
from .schema import Event, Snapshot


# Initial state shape (v0 fixed structure)
INITIAL_STATE: Dict[str, Any] = {
    "messages": [],
    "decisions": [],
    "system": {},
}


def apply_event(
    state: Dict[str, Any],
    event: Event,
) -> Dict[str, Any]:
    """
    Pure state transformation.
    
    Invariant: 
      - Input state is never mutated
      - Output is a new dict (immutable contract)
      - Only allowed mutations: append to messages/decisions, set system keys
    
    Event type handlers:
      - user_message: append to messages
      - assistant_message: append to messages
      - system: merge payload into system dict
      - decision: append to decisions
    """
    # Deep copy input state (defensive programming)
    new_state = {
        "messages": state["messages"][:],
        "decisions": state["decisions"][:],
        "system": state["system"][:],
    }
    
    if event.type == "user_message":
        # Append user message with event context
        new_state["messages"].append({
            "id": event.event_id,
            "timestamp": event.timestamp,
            "type": event.type,
            "content": event.payload.get("content", ""),
            "metadata": event.payload.get("metadata", {}),
        })
    
    elif event.type == "assistant_message":
        # Append assistant message
        new_state["messages"].append({
            "id": event.event_id,
            "timestamp": event.timestamp,
            "type": event.type,
            "content": event.payload.get("content", ""),
            "metadata": event.payload.get("metadata", {}),
        })
    
    elif event.type == "system":
        # Merge system payload (idempotent upsert)
        system_data = new_state["system"]
        system_data.update({
            k: v for k, v in event.payload.items()
            if not k.startswith("__")  # Filter internal keys
        })
    
    elif event.type == "decision":
        # Append decision
        new_state["decisions"].append({
            "id": event.event_id,
            "timestamp": event.timestamp,
            "type": event.type,
            "content": event.payload.get("content", ""),
            "metadata": event.payload.get("metadata", {}),
        })
    
    return new_state


def create_initial_snapshot(state_id: str, timestamp: str) -> Snapshot:
    """
    Create initial empty snapshot for replay.
    """
    return Snapshot(
        state_id=state_id,
        timestamp=timestamp,
        messages=[],
        decisions=[],
        system={},
    )