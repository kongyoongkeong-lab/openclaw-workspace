"""
Replay Kernel v0 - Determinism Test Suite
==================================================
Core assertions:
  
  1. replay(log) == replay(log)  [Determinism]
  2. replay(log_a) != replay(log_b)  [Ordering sensitivity]
  3. State shape stability
  
No external dependencies, no mocking, pure Python.
"""

import datetime
import json
from typing import List

from replay_kernel.schema import Event, Snapshot
from replay_kernel.reducer import apply_event
from replay_kernel.replay import replay, replay_with_logging


def create_test_events() -> List[Event]:
    """
    Create sample event log for replay testing.
    """
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    return [
        Event("ev_user_1", now, "user_message", {"content": "Hello", "metadata": {"session": "s1"}}),
        Event("ev_assist_1", now, "assistant_message", {"content": "Hi there", "metadata": {"model": "qwen"} }),
        Event("ev_sys_1", now, "system", {"version": "1.0.0", "uptime": 0}),
        Event("ev_decision_1", now, "decision", {"content": "route-to-tools", "metadata": {"reason": "user-asked"}}),
    ]


def test_determinism():
    """
    Core replay kernel test: same input → same output.
    
    This is the definition of a deterministic state machine.
    """
    events = create_test_events()
    
    # Replay twice
    result1 = replay(events)
    result2 = replay(events)
    
    # Assert structural equality
    assert result1 == result2, "Replay is NOT deterministic!"
    
    print("✅ Determinism test passed")
    print(f"   Messages: {len(result1.messages)}")
    print(f"   Decisions: {len(result1.decisions)}")
    print(f"   System keys: {len(result1.system)}")


def test_ordering_sensitivity():
    """
    Verify that event ordering affects state.
    
    Non-deterministic ordering should produce different states.
    """
    events = create_test_events()
    
    # Original order
    result1 = replay(events)
    
    # Reverse order
    reversed_events = events[::-1]
    result2 = replay(reversed_events)
    
    # States should differ
    assert result1 != result2, "Ordering should affect state!"
    
    print("✅ Ordering sensitivity test passed")


def test_state_shape_stability():
    """
    Verify state shape remains stable.
    """
    events = create_test_events()
    result = replay(events)
    
    # Check shape invariants
    assert "messages" in result.to_dict()
    assert "decisions" in result.to_dict()
    assert "system" in result.to_dict()
    
    # Type checks
    assert isinstance(result.messages, list)
    assert isinstance(result.decisions, list)
    assert isinstance(result.system, dict)
    
    print("✅ State shape stability test passed")


def test_pure_state_transformation():
    """
    Verify that apply_event does not mutate input state.
    """
    initial = {"messages": [], "decisions": [], "system": {"v": "1.0"}}
    initial_copy = dict(initial)  # Shallow copy
    
    event = Event("ev1", "now", "user_message", {"content": "test"})
    result = apply_event(initial, event)
    
    # Input should be unchanged
    assert initial == initial_copy, "apply_event mutated input state!"
    
    # Result should be new object
    assert result is not initial, "apply_event should return new state!"
    
    print("✅ Pure state transformation test passed")


def test_event_id_uniqueness():
    """
    Verify event IDs are unique within a replay.
    """
    events = create_test_events()
    result = replay(events)
    
    message_ids = [m["id"] for m in result.messages]
    decision_ids = [d["id"] for d in result.decisions]
    
    assert len(message_ids) == len(set(message_ids)), "Duplicate message IDs!"
    assert len(decision_ids) == len(set(decision_ids)), "Duplicate decision IDs!"
    
    print("✅ Event ID uniqueness test passed")


def test_system_merging():
    """
    Verify system payload merges correctly.
    """
    events = create_test_events()
    
    # Add more system events
    now = datetime.datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    system_events = [
        Event("ev_sys_2", now, "system", {"feature": "flag-a"}),
        Event("ev_sys_3", now, "system", {"feature": "flag-b"}),
    ]
    
    all_events = events + system_events
    result = replay(all_events)
    
    # System should have merged keys
    assert "version" in result.system
    assert "uptime" in result.system
    assert "feature" in result.system
    
    print("✅ System merging test passed")


def run_all_tests():
    """
    Execute full test suite.
    """
    print("=" * 60)
    print("Replay Kernel v0 - Determinism Test Suite")
    print("=" * 60)
    
    tests = [
        test_determinism,
        test_ordering_sensitivity,
        test_state_shape_stability,
        test_pure_state_transformation,
        test_event_id_uniqueness,
        test_system_merging,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)