#!/usr/bin/env python3
"""
3A-4 ingest_event() Prototype
Hard-rejection pipeline with quarantine stub.
Tests: duplicate, gap, tamper, reorder.
"""

import json
import hmac
import hashlib
import os
import uuid
from datetime import datetime

REPLAY_WINDOW = 5 * 60 * 1000  # 5 minutes in ms
MAX_SEQ_DIFF = 3  # Allowed gap in sequence_id

def compute_hmac(payload: str, seq_id: int, key: str) -> str:
    """Compute HMAC-SHA256 for payload."""
    msg = f"{seq_id}:{payload}".encode()
    return hmac.new(key.encode(), msg, hashlib.sha256).hexdigest()

def check_duplicate(event_id: str, registry_path: str) -> bool:
    """Check if event_id already exists in registry."""
    try:
        registry = json.loads(open(registry_path).read())
        for stream_events in registry.get("chains", {}).values():
            for evt in stream_events:
                if evt.get("event_id") == event_id:
                    return True
        return False
    except:
        return False

def is_gapless(prev: dict, curr: dict, max_seq_diff: int) -> bool:
    """Check if sequence gap is within tolerance."""
    seq_diff = curr["sequence_id"] - prev["sequence_id"]
    return abs(seq_diff) <= max_seq_diff

# Paths
CHAIN_REGISTRY = "/home/jason2ykk/.openclaw/workspace/tools/chain_registry.json"
QUARANTINE_DIR = "/home/jason2ykk/.openclaw/workspace/tools/quarantine"
STORAGE_PATH = "/home/jason2ykk/.openclaw/workspace/telemetry/telemetry.jsonl"

# Reject reasons
REPLAY_DETECTED = "replay_detected"
GAP_DETECTED = "gap_detected"
HASH_MISMATCH = "hash_mismatch"
INVALID_SCHEMA = "invalid_schema"

def ingest_event(event: dict) -> tuple:
    """
    ingest_event(event: dict) -> (accepted: bool, reason: str, event_id: str)
    
    0. Schema validation (fail fast)
    1. Replay protection
    2. Gap detection
    3. Hash chain verification
    4. Commit (ONLY after all checks pass)
    """
    # 0. Schema validation
    required_fields = ["source_id", "stream_id", "sequence_id", "timestamp", "payload_hash", "payload", "key"]
    missing = [f for f in required_fields if f not in event]
    if missing:
        return (False, INVALID_SCHEMA, event.get("id") or str(uuid.uuid4()))
    
    # Ensure monotonic sequence_id (int, not str)
    if not isinstance(event["sequence_id"], int):
        return (False, INVALID_SCHEMA, event.get("id") or str(uuid.uuid4()))
    
    # 1. Replay protection
    event_id = event.get("id") or hashlib.sha256(
        f"{event['source_id']}-{event['stream_id']}-{event['sequence_id']}".encode()
    ).hexdigest()
    
    if check_duplicate(event_id, CHAIN_REGISTRY):
        return (False, REPLAY_DETECTED, event_id)
    
    # 2. Gap detection (requires previous event)
    stream_id = event["stream_id"]
    try:
        registry = json.loads(open(CHAIN_REGISTRY).read())
        prev = registry.get("chains", {}).get(stream_id, [])
        if prev:
            prev_event = prev[-1]
            if not is_gapless(prev_event, event, max_seq_diff=MAX_SEQ_DIFF):
                return (False, GAP_DETECTED, event_id)
    except Exception:
        pass  # No chain yet, allow first event
    
    # 3. Hash chain verification
    try:
        expected_hash = compute_hmac(json.dumps(event["payload"], sort_keys=True), event["sequence_id"], event["key"])
    except Exception:
        expected_hash = hashlib.sha256(json.dumps(event["payload"], sort_keys=True).encode()).hexdigest()
    
    if event["payload_hash"] != expected_hash:
        return (False, HASH_MISMATCH, event_id)
    
    # 4. Commit (append to storage + update registry)
    try:
        # Ensure storage directory exists
        os.makedirs(os.path.dirname(STORAGE_PATH), exist_ok=True)
        # Append to storage
        with open(STORAGE_PATH, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        # Update registry (atomic: read-modify-write)
        registry = json.loads(open(CHAIN_REGISTRY).read())
        registry["chains"][stream_id].append({
            "sequence_id": event["sequence_id"],
            "payload_hash": event["payload_hash"],
            "timestamp": event["timestamp"],
            "event_id": event_id
        })
        with open(CHAIN_REGISTRY, "w") as f:
            json.dump(registry, f, indent=2)
        
        # Stub: quarantine (not used yet)
        os.makedirs(QUARANTINE_DIR, exist_ok=True)
        
        return (True, "", event_id)
    except Exception as e:
        return (False, f"commit_error: {e}", event_id)

def run_tests():
    """Run 4 test cases: duplicate, gap, tamper, reorder."""
    print("🧪 3A-4 ingest_event() — Running 4 Tests")
    print("=" * 60)
    
    # Initialize empty registry and storage
    registry = {"chains": {}}
    json.dump(registry, open(CHAIN_REGISTRY, "w"), indent=2)
    
    # Clear storage file
    open(STORAGE_PATH, "w").close()
    
    # Helper to compute hash for test events
    def test_hash(payload, seq_id, key):
        return compute_hmac(json.dumps(payload, sort_keys=True), seq_id, key)
    
    print("\n[Test 1] First Event (Should Accept)")
    event1 = {
        "id": "e1",
        "source_id": "sensor_a",
        "stream_id": "temp",
        "sequence_id": 100,
        "timestamp": "2026-05-10T17:28:00Z",
        "payload": {"temp": 23.5, "unit": "c"},
        "key": "secret-key",
        "payload_hash": test_hash({"temp": 23.5, "unit": "c"}, 100, "secret-key")
    }
    accepted1, reason1, eid1 = ingest_event(event1)
    print(f"  First event: accepted={accepted1}, reason={reason1}")
    
    print("\n[Test 2] Duplicate Event (Should Reject)")
    # Try duplicate
    accepted2, reason2, eid2 = ingest_event(event1)
    print(f"  Duplicate event: accepted={accepted2}, reason={reason2}")
    assert not accepted2 and reason2 == REPLAY_DETECTED, f"Test 2 failed: got reason={reason2}"
    
    print("\n[Test 3] Gap in Sequence (Should Reject)")
    event3a = {
        "id": "e3a",
        "source_id": "sensor_a",
        "stream_id": "temp",
        "sequence_id": 101,
        "timestamp": "2026-05-10T17:29:00Z",
        "payload": {"temp": 23.6},
        "key": "secret-key",
        "payload_hash": test_hash({"temp": 23.6}, 101, "secret-key")
    }
    accepted3a, reason3a, eid3a = ingest_event(event3a)
    print(f"  Event 101: accepted={accepted3a}, reason={reason3a}")
    
    event3b = {
        "id": "e3b",
        "source_id": "sensor_a",
        "stream_id": "temp",
        "sequence_id": 105,  # Gap: 101 → 105
        "timestamp": "2026-05-10T17:35:00Z",
        "payload": {"temp": 24.0},
        "key": "secret-key",
        "payload_hash": test_hash({"temp": 24.0}, 105, "secret-key")
    }
    accepted3b, reason3b, eid3b = ingest_event(event3b)
    print(f"  Event 105: accepted={accepted3b}, reason={reason3b}")
    assert not accepted3b and reason3b == GAP_DETECTED, f"Test 3 failed: got reason={reason3b}"
    
    print("\n[Test 4] Tampered Payload (Should Reject)")
    event4 = {
        "id": "e4",
        "source_id": "sensor_a",
        "stream_id": "temp",
        "sequence_id": 102,
        "timestamp": "2026-05-10T17:30:00Z",
        "payload": {"temp": 23.7, "unit": "c"},
        "key": "secret-key",
        "payload_hash": "tampered"  # Wrong hash
    }
    accepted4, reason4, eid4 = ingest_event(event4)
    print(f"  Result: accepted={accepted4}, reason={reason4}")
    assert not accepted4 and reason4 == HASH_MISMATCH, f"Test 4 failed: got reason={reason4}"
    
    print("\n[Test 5] Out-of-Order Event (Should Reject - gap)")
    event5a = {
        "id": "e5a",
        "source_id": "sensor_b",
        "stream_id": "pressure",
        "sequence_id": 200,
        "timestamp": "2026-05-10T17:31:00Z",
        "payload": {"pressure": 101.3},
        "key": "secret-key",
        "payload_hash": test_hash({"pressure": 101.3}, 200, "secret-key")
    }
    accepted5a, reason5a, eid5a = ingest_event(event5a)
    print(f"  Event 200: accepted={accepted5a}, reason={reason5a}")
    
    event5b = {
        "id": "e5b",
        "source_id": "sensor_b",
        "stream_id": "pressure",
        "sequence_id": 199,  # Out-of-order: 200 → 199
        "timestamp": "2026-05-10T17:29:00Z",
        "payload": {"pressure": 101.2},
        "key": "secret-key",
        "payload_hash": test_hash({"pressure": 101.2}, 199, "secret-key")
    }
    accepted5b, reason5b, eid5b = ingest_event(event5b)
    print(f"  Event 199: accepted={accepted5b}, reason={reason5b}")
    assert not accepted5b and reason5b == GAP_DETECTED, f"Test 5 failed: got reason={reason5b}"
    
    print("\n✅ All 5 tests passed!")
    print("   Hard-rejection logic verified.")
    print("   Quarantine stub in place (for rejected events).")
    return True

if __name__ == "__main__":
    run_tests()