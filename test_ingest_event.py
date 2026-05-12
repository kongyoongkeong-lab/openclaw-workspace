#!/usr/bin/env python3
"""Pressure-test ingest_event()"""

import ingest_event
import hashlib
import time


def test_1_valid_event():
    """Test 1: Valid event should pass."""
    payload = {
        "event_id": "evt-001",
        "event_type": "user_action",
        "timestamp": int(time.time()),
        "payload": {"action": "click", "button": "submit"},
        "source": "api",
        "chain_prev": [],
        "chain_integrity": {}
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("=" * 60)
    print("TEST 1: Valid Event")
    print(f"Success: {result.success}")
    print(f"Event ID: {result.event.event_id if result.event else None}")
    print(f"Hash Chain: {result.event.hash_chain if result.event else None}")
    print("=" * 60)
    return result.success


def test_2_missing_field():
    """Test 2: Missing required field should reject."""
    payload = {
        "event_id": "evt-002",
        "event_type": "user_action",
        # Missing timestamp
        "payload": {"action": "click"},
        "source": "api"
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("\n" + "=" * 60)
    print("TEST 2: Missing Field")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Rejected: {result.rejected}")
    print("=" * 60)
    return not result.success  # Should fail


def test_3_future_timestamp():
    """Test 3: Far future timestamp should reject."""
    payload = {
        "event_id": "evt-003",
        "event_type": "user_action",
        "timestamp": int(time.time()) + 2678400,  # +31 days
        "payload": {"action": "click"},
        "source": "api",
        "chain_prev": [],
        "chain_integrity": {}
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("\n" + "=" * 60)
    print("TEST 3: Far Future Timestamp")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Rejected: {result.rejected}")
    print("=" * 60)
    return not result.success  # Should fail


def test_4_invalid_event_type():
    """Test 4: Unknown event type should reject."""
    payload = {
        "event_id": "evt-004",
        "event_type": "magic_wand",  # Invalid
        "timestamp": int(time.time()),
        "payload": {"action": "click"},
        "source": "api",
        "chain_prev": [],
        "chain_integrity": {}
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("\n" + "=" * 60)
    print("TEST 4: Invalid Event Type")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Rejected: {result.rejected}")
    print("=" * 60)
    return not result.success  # Should fail


def test_5_chain_break():
    """Test 5: Broken chain (missing previous event) should reject."""
    payload = {
        "event_id": "evt-005",
        "event_type": "user_action",
        "timestamp": int(time.time()),
        "payload": {"action": "click"},
        "source": "api",
        "chain_prev": ["evt-missing-001"],  # This doesn't exist
        "chain_integrity": {}
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("\n" + "=" * 60)
    print("TEST 5: Broken Chain (Missing Previous Event)")
    print(f"Success: {result.success}")
    print(f"Error: {result.error}")
    print(f"Rejected: {result.rejected}")
    print("=" * 60)
    return not result.success  # Should fail


def test_6_valid_chain():
    """Test 6: Valid chain with proper chain_integrity."""
    import hashlib
    # Simulate a chain of 3 previous events with proper 16-char hashes
    chain_prev = ["evt-prev-001", "evt-prev-002", "evt-prev-003"]
    chain_integrity = {
        "evt-prev-001": hashlib.sha256("evt-prev-001:user_action:123456:api".encode()).hexdigest()[:16],
        "evt-prev-002": hashlib.sha256("evt-prev-002:user_action:123457:api".encode()).hexdigest()[:16],
        "evt-prev-003": hashlib.sha256("evt-prev-003:user_action:123458:api".encode()).hexdigest()[:16]
    }
    print(f"Chain Integrity: {chain_integrity}")
    print(f"Chain Prev: {chain_prev}")
    
    payload = {
        "event_id": "evt-006",
        "event_type": "system_event",
        "timestamp": int(time.time()),
        "payload": {"type": "heartbeat"},
        "source": "internal",
        "chain_prev": chain_prev,
        "chain_integrity": chain_integrity
    }
    
    result = ingest_event.ingest_event(payload)
    
    print("\n" + "=" * 60)
    print("TEST 6: Valid Chain with Proper Integrity")
    print(f"Success: {result.success}")
    print(f"Hash Chain Length: {len(result.event.hash_chain) if result.event else 0}")
    print(f"Hash Chain: {result.event.hash_chain if result.event else None}")
    print("=" * 60)
    return result.success


if __name__ == "__main__":
    results = []
    
    # Run all tests
    results.append(("Valid Event", test_1_valid_event()))
    results.append(("Missing Field", test_2_missing_field()))
    results.append(("Future Timestamp", test_3_future_timestamp()))
    results.append(("Invalid Type", test_4_invalid_event_type()))
    results.append(("Broken Chain", test_5_chain_break()))
    results.append(("Valid Chain", test_6_valid_chain()))
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("=" * 60)
