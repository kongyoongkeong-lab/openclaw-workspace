#!/usr/bin/env python3
"""
Quick test runner for Replay Kernel v0
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/replay_kernel")

from events.schema import Event, EventType, make_event
from kernel.reducer import State, apply_event
from kernel.state import StateValidator
from kernel.replay import ReplayKernel, create_kernel

def test_basic_replay():
    """Test basic replay determinism."""
    print("[TEST] Basic replay determinism...")
    
    kernel1 = create_kernel()
    kernel2 = create_kernel()
    
    now = datetime.now(timezone.utc)
    events = [
        make_event("evt_0001", EventType.SYSTEM, {"system": "init"}, now),
        make_event("evt_0002", EventType.USER_MESSAGE, {"message": "hello"}, now),
        make_event("evt_0003", EventType.TOOL, {"tool": "shell"}, now),
    ]
    
    for e in events:
        kernel1.append_event(e)
        kernel2.append_event(e)
    
    state1 = kernel1.replay()
    state2 = kernel2.replay()
    
    # Compare
    assert state1.messages == state2.messages, "Messages differ"
    assert state1.tools == state2.tools, "Tools differ"
    assert StateValidator.compute_hash(state1) == StateValidator.compute_hash(state2), "Hashes differ"
    
    print("  ✓ PASS: States match")
    return True

def test_immutable_reducer():
    """Test that reducer never mutates input."""
    print("[TEST] Immutable reducer...")
    
    original = State(messages=["msg1"])
    event = make_event("evt_0001", EventType.USER_MESSAGE, {"message": "msg2"})
    
    result = apply_event(original, event)
    
    assert original.messages == ["msg1"], "Original state was mutated!"
    assert result.messages == ["msg1", "msg2"], "Result doesn't have new message"
    
    print("  ✓ PASS: Input state unchanged")
    return True

def test_state_export():
    """Test state export/import."""
    print("[TEST] State export/import...")
    
    kernel = create_kernel()
    now = datetime.now(timezone.utc)
    event = make_event("evt_0001", EventType.SYSTEM, {"system": "test"})
    kernel.append_event(event)
    
    # Export
    lines = kernel.export_log()
    assert len(lines) == 1, "Export should have 1 line"
    
    # Import
    new_kernel = create_kernel()
    new_kernel.load_log(lines)
    
    assert len(new_kernel.event_log) == 1, "Import should restore event"
    
    print("  ✓ PASS: Export/import works")
    return True

def test_target_time_replay():
    """Test replay with target_time cutoff."""
    print("[TEST] Target time replay...")
    
    kernel = create_kernel()
    now = datetime.now(timezone.utc)
    
    events = [
        make_event("evt_0001", EventType.SYSTEM, {"v": "1"}, now),
        make_event("evt_0002", EventType.SYSTEM, {"v": "2"},
                   now.replace(second=now.second + 1)),
        make_event("evt_0003", EventType.SYSTEM, {"v": "3"},
                   now.replace(second=now.second + 2)),
    ]
    for e in events:
        kernel.append_event(e)
    
    target = events[1].timestamp
    state = kernel.replay(target_time=target)
    
    assert len(state.systems) == 2, f"Should have 2 systems, got {len(state.systems)}"
    
    print("  ✓ PASS: Target time cutoff works")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("Replay Kernel v0 — Test Suite")
    print("=" * 60)
    
    tests = [
        test_basic_replay,
        test_immutable_reducer,
        test_state_export,
        test_target_time_replay,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAIL: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    
    sys.exit(0 if failed == 0 else 1)
