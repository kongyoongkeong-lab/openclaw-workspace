"""
Replay Engine — Deterministic State Reconstruction
Replay Kernel v0 — Deterministic State Machine
"""

import sys
from datetime import datetime, timezone
import json

sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/replay_kernel")

from events.schema import Event, make_event
from kernel.reducer import apply_event_batch, State
from kernel.state import StateValidator

class ReplayKernel:
    """
    Deterministic state replay kernel.
    
    Core principle:
    state(t) = replay(event_log[0..t])
    
    This eliminates "reset sensation" by ensuring:
    - All state is reproducible from event log
    - No dependency on context window size
    - Pure function replay (no side effects)
    """
    
    def __init__(self, initial_state=None):
        """
        Initialize with optional initial state.
        
        Args:
            initial_state: Starting state (defaults to empty)
        """
        self.initial_state = initial_state or State.empty()
        self.event_log = []
    
    def append_event(self, event):
        """Append event to log (append-only)."""
        self.event_log.append(event)
    
    def append_events(self, events):
        """Append multiple events."""
        self.event_log.extend(events)
    
    def replay(self, target_time=None):
        """
        Deterministic replay from initial state to target time.
        
        Args:
            target_time: Replay up to this timestamp (optional).
                         If None, replay all events.
        
        Returns:
            State at target_time (or final state)
        """
        if not self.event_log:
            return self.initial_state.copy()
        
        # Filter events up to target_time if specified
        cutoff = target_time or datetime.max.replace(tzinfo=timezone.utc)
        filtered_events = [
            e for e in self.event_log
            if e.timestamp <= cutoff
        ]
        
        return apply_event_batch(self.initial_state, filtered_events)
    
    def snapshot(self):
        """
        Get current snapshot of (event_log, replayed_state).
        
        Used for validation and testing.
        """
        state = self.replay()
        return self.event_log.copy(), state
    
    def export_log(self):
        """Export event log as string lines (for persistence)."""
        return [e.to_log_line() for e in self.event_log]
    
    def load_log(self, lines):
        """
        Load event log from string lines.
        
        Args:
            lines: List of log lines from export_log()
        
        Each line format: {event_id}|{timestamp}|{type}|{payload}
        """
        from events.schema import Event, EventType
        for line in lines:
            parts = line.split("|")
            event_id = parts[0]
            timestamp = datetime.fromisoformat(parts[1])
            event_type_str = parts[2]
            payload = parts[3] if len(parts) > 3 else {}
            
            event_type = EventType(event_type_str)
            
            self.event_log.append(Event(
                event_id=event_id,
                timestamp=timestamp,
                event_type=event_type,
                payload=payload,
            ))

def create_kernel(initial_state=None):
    """Factory function for replay kernels."""
    return ReplayKernel(initial_state=initial_state)
