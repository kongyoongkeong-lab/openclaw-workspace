"""
Replay Kernel v0 - Core Schema Definitions
==================================================
Event types (max 4):
  - user_message
  - assistant_message
  - system
  - decision

Strict constraints:
  - event_id: immutable identifier
  - timestamp: ISO-8601 UTC
  - type: enum (user_message|assistant_message|system|decision)
  - payload: immutable snapshot
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet


@dataclass(frozen=True)
class Event:
    """
    Immutable event record.
    
    Field invariants:
      - event_id: Unique, non-None, never changes
      - timestamp: ISO-8601 UTC, derived from system clock at emission
      - type: One of ['user_message', 'assistant_message', 'system', 'decision']
      - payload: Immutable snapshot (no mutable state)
    """
    event_id: str
    timestamp: str  # ISO-8601 UTC string
    type: str
    payload: Dict[str, Any]
    
    def __post_init__(self) -> None:
        """Validate event integrity at construction time."""
        if not self.event_id:
            raise ValueError("event_id cannot be empty")
        if self.type not in ("user_message", "assistant_message", "system", "decision"):
            raise ValueError(f"Invalid event type: {self.type}")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")


@dataclass(frozen=True)
class Snapshot:
    """
    Immutable state snapshot for determinism verification.
    
    Shape:
      {
        "messages": List[Dict],
        "decisions": List[Dict],
        "system": Dict
      }
    """
    state_id: str
    timestamp: str
    messages: list = field(default_factory=list)
    decisions: list = field(default_factory=list)
    system: dict = field(default_factory=dict)
    
    def __eq__(self, other: "Snapshot") -> bool:
        """
        Structural equality check for determinism verification.
        
        Compares:
          - state_id
          - timestamp
          - messages (deep equality)
          - decisions (deep equality)
          - system (deep equality)
        """
        if not isinstance(other, Snapshot):
            return False
        return (self.state_id == other.state_id and
                self.timestamp == other.timestamp and
                self.messages == other.messages and
                self.decisions == other.decisions and
                self.system == other.system)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for JSON serialization."""
        return {
            "state_id": self.state_id,
            "timestamp": self.timestamp,
            "messages": self.messages,
            "decisions": self.decisions,
            "system": self.system,
        }