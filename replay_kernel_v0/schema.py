"""Replay Kernel v0 immutable event schema.

Semantics are intentionally minimal and frozen for deterministic replay tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

ALLOWED_EVENT_TYPES = frozenset({
    "user_message",
    "assistant_message",
    "system",
    "decision",
})


@dataclass(frozen=True)
class Event:
    """Immutable replay event."""

    event_id: str
    timestamp: str
    type: str
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if not self.timestamp:
            raise ValueError("timestamp cannot be empty")
        if self.type not in ALLOWED_EVENT_TYPES:
            raise ValueError(f"invalid event type: {self.type}")
        if not isinstance(self.payload, Mapping):
            raise ValueError("payload must be a mapping")
