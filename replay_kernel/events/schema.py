"""
Event Schema (Immutable)
Replay Kernel v0 — Deterministic State Machine
"""

import dataclasses
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

class EventType(Enum):
    """Event types for replay kernel."""
    USER_MESSAGE = "user_message"
    SYSTEM = "system"
    TOOL = "tool"
    AGENT_TURN = "agent_turn"
    DIVERGENCE = "divergence"

@dataclasses.dataclass(frozen=True)
class Event:
    """Immutable event representing a system state transition."""
    
    event_id: str
    timestamp: datetime
    event_type: EventType
    payload: dict[str, Any]
    metadata: Optional[dict[str, Any]] = None
    
    def to_dict(self) -> dict:
        """Convert to dict for logging."""
        return dataclasses.asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Reconstruct event from dict (for replay)."""
        return cls(
            event_id=data["event_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=EventType(data["event_type"]),
            payload=data["payload"],
            metadata=data.get("metadata"),
        )
    
    def to_log_line(self) -> str:
        """Compact JSON-serializable representation."""
        return f'{self.event_id}|{self.timestamp.isoformat()}|{self.event_type.value}|{self.payload}'

def make_event(event_id: str, event_type: EventType, payload: dict,
                timestamp: Optional[datetime] = None,
                metadata: Optional[dict] = None) -> Event:
    """Factory function for immutable events."""
    ts = timestamp or datetime.now(timezone.utc)
    return Event(
        event_id=event_id,
        timestamp=ts,
        event_type=event_type,
        payload=payload,
        metadata=metadata,
    )
