"""
Replay Kernel v0 - Deterministic Replay Engine
==================================================
Minimal replay:
  
  for e in log:
    state = apply_event(state, e)
  
No fancy kernel, no side effects, no external dependencies.
"""

from typing import List, Dict
from .reducer import apply_event, create_initial_snapshot
from .schema import Snapshot


def replay(
    events: List["Event"],
    state_id: str = "replay_v0",
) -> Snapshot:
    """
    Deterministic state replay.
    
    Contract:
      - Input events must be immutable
      - Replay order matters (non-deterministic if order changes)
      - Output is a pure function of (events, initial_state)
    
    Usage:
      events = [
        Event("e1", "2026-01-01T00:00:00Z", "user_message", 
               {"content": "Hello"}),
        Event("e2", "2026-01-01T00:01:00Z", "assistant_message",
               {"content": "Hi there"}),
      ]
      result = replay(events)
      assert replay(events) == replay(events)  # Determinism check
    """
    state = create_initial_snapshot(state_id, events[0].timestamp if events else "")
    
    for event in events:
        state = apply_event(state, event)
    
    return Snapshot(
        state_id=state_id,
        timestamp=events[-1].timestamp if events else state.timestamp,
        messages=state["messages"],
        decisions=state["decisions"],
        system=state["system"],
    )


def replay_with_logging(
    events: List["Event"],
    log_prefix: str = "[REPLAY]",
) -> Snapshot:
    """
    Replay with optional debug logging (for development only).
    
    WARNING: This breaks determinism if logging output is captured.
    Use only for debugging, never in production replay path.
    """
    print(f"{log_prefix} Starting replay with {len(events)} events")
    
    snapshot = replay(events)
    
    print(f"{log_prefix} Replay complete. Messages: {len(snapshot.messages)}, "
          f"Decisions: {len(snapshot.decisions)}")
    
    return snapshot