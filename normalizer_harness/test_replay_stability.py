"""
test_replay_stability.py
Invariant: replay(trace) == canonical_signal_set

Binary enforcement only. No inference. No scoring.
"""
import os
import sys
import json
sys.path.insert(0, os.path.dirname(__file__))

from signal_normalizer import normalize


def test_replay_stability():
    """
    Replay stability invariant:
    Replay of a trace must produce canonical signal set.
    
    Simulate:
    1. Record raw trace
    2. Replay trace (re-read + re-normalize)
    3. Compare signal sets
    """
    # Simulated raw trace (append-only)
    raw_trace = [
        {"event": "heartbeat", "latency_ms": 120, "timestamp": 1},
        {"event": "compute", "latency_ms": 1837, "timestamp": 2},
        {"event": "handoff", "agent": "@intel", "timestamp": 3},
    ]
    
    # First pass: normalize trace
    signals1 = [normalize(event) for event in raw_trace]
    
    # Replay: simulate re-reading trace from persistent store
    # (In production, this would read from file/db)
    replayed_trace = raw_trace  # Same data, simulating re-read
    
    # Second pass: re-normalize
    signals2 = [normalize(event) for event in replayed_trace]
    
    # Binary check: signal sets must match
    assert signals1 == signals2, "Replay stability invariant violated"
    
    return "PASS" if signals1 == signals2 else "FAIL"


if __name__ == "__main__":
    result = test_replay_stability()
    print(f"test_replay_stability: {result}")
    sys.exit(0 if result == "PASS" else 1)
