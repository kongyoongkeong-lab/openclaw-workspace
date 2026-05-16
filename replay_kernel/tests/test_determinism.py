"""
Determinism Tests — Replay Kernel v0
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from datetime import datetime, timezone

from events.schema import Event, EventType, make_event
from kernel.replay import ReplayKernel, create_kernel
from kernel.reducer import State, apply_event
from kernel.state import StateValidator

class TestDeterminism(unittest.TestCase):
    """Test that replay is deterministic across independent runs."""
    
    def setUp(self):
        self.kernel1 = create_kernel()
        self.kernel2 = create_kernel()
        
        # Create sample event log
        now = datetime.now(timezone.utc)
        self.events = [
            make_event("evt_0001", EventType.SYSTEM, {
                "action": "system_init",
                "system": "discord_bot",
            }, now),
            make_event("evt_0002", EventType.USER_MESSAGE, {
                "message": "Hello, system!",
            }, now),
            make_event("evt_0003", EventType.TOOL, {
                "tool": "shell",
                "command": "ls",
            }, now),
        ]
    
    def test_independent_replay(self):
        """Independent replays should produce identical state."""
        for event in self.events:
            self.kernel1.append_event(event)
            self.kernel2.append_event(event)
        
        state1 = self.kernel1.replay()
        state2 = self.kernel2.replay()
        
        # States must be identical
        self.assertEqual(state1.messages, state2.messages)
        self.assertEqual(state1.tools, state2.tools)
        self.assertEqual(StateValidator.compute_hash(state1),
                        StateValidator.compute_hash(state2))
    
    def test_same_log_same_state(self):
        """Same event log always produces same state."""
        state_a = self.kernel1.replay()
        state_b = self.kernel1.replay()
        
        self.assertEqual(state_a.to_dict(), state_b.to_dict())
    
    def test_state_hash_consistency(self):
        """State hash should be consistent."""
        state = self.kernel1.replay()
        hash1 = StateValidator.compute_hash(state)
        hash2 = StateValidator.compute_hash(state)
        
        self.assertEqual(hash1, hash2)

class TestReducerImmutability(unittest.TestCase):
    """Test that reducer never mutates input state."""
    
    def test_apply_event_immutable(self):
        """apply_event should not mutate input state."""
        original_state = State(messages=["msg1"])
        event = make_event("evt_0001", EventType.USER_MESSAGE, {"message": "msg2"})
        
        result = apply_event(original_state, event)
        
        # Original state unchanged
        self.assertEqual(original_state.messages, ["msg1"])
        # Result has new message
        self.assertEqual(result.messages, ["msg1", "msg2"])

class TestTargetTimeReplay(unittest.TestCase):
    """Test replay with target_time cutoff."""
    
    def setUp(self):
        self.kernel = create_kernel()
        self.now = datetime.now(timezone.utc)
        
        # Events at different times
        self.events = [
            make_event("evt_0001", EventType.SYSTEM, {"system": "v1"}, self.now),
            make_event("evt_0002", EventType.SYSTEM, {"system": "v2"},
                       self.now.replace(second=self.now.second + 1)),
            make_event("evt_0003", EventType.SYSTEM, {"system": "v3"},
                       self.now.replace(second=self.now.second + 2)),
        ]
        for e in self.events:
            self.kernel.append_event(e)
    
    def test_replay_up_to_t1(self):
        """Replay should stop at target_time."""
        target = self.events[1].timestamp
        state = self.kernel.replay(target_time=target)
        
        # Should only have first two events
        self.assertEqual(len(state.systems), 2)

if __name__ == "__main__":
    unittest.main()
