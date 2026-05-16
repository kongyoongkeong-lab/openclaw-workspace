"""Replay Kernel v0 pure reducer.

Freeze rule: reducer semantics stay minimal and deterministic.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .schema import Event


def initial_state() -> dict[str, Any]:
    """Return the fixed v0 initial state shape."""
    return {
        "messages": [],
        "decisions": [],
        "system": {},
    }


def apply_event(state: dict[str, Any], event: Event) -> dict[str, Any]:
    """Apply one event without mutating the input state."""
    next_state = {
        "messages": deepcopy(state["messages"]),
        "decisions": deepcopy(state["decisions"]),
        "system": deepcopy(state["system"]),
    }

    if event.type in ("user_message", "assistant_message"):
        next_state["messages"].append({
            "id": event.event_id,
            "timestamp": event.timestamp,
            "type": event.type,
            "content": event.payload.get("content", ""),
            "metadata": deepcopy(event.payload.get("metadata", {})),
        })
    elif event.type == "decision":
        next_state["decisions"].append({
            "id": event.event_id,
            "timestamp": event.timestamp,
            "type": event.type,
            "content": event.payload.get("content", ""),
            "metadata": deepcopy(event.payload.get("metadata", {})),
        })
    elif event.type == "system":
        next_state["system"].update({
            key: deepcopy(value)
            for key, value in event.payload.items()
            if not key.startswith("__")
        })

    return next_state
