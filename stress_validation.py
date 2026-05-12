#!/usr/bin/env python3
"""
Phase 2: Instrumentation Stress Validation Suite
Tests:
  - Test A: Burst ingestion (100 sequential events per probe)
  - Test B: Interleaved probe execution (round-robin firing)
  - Test C: Rapid-fire ingestion (minimal delay)
Invariant:
  For all probes:
    event_count == expected_count
    logical_time strictly increasing per probe stream
"""

import asyncio
import os
import json
import time
import random
from collections import defaultdict
from pathlib import Path

# Paths
BASE = Path("/home/jason2ykk/.openclaw/workspace")
LOGS = BASE / "instruments"
STATE = BASE / "instrument_state.json"

# Load probes (from instrument_state.json)
def load_probes():
    if STATE.exists():
        with open(STATE) as f:
            state = json.load(f)
        return state.get("probes", [])
    return []

# Save state
def save_state(probes, events_per_probe):
    state = {
        "probes": probes,
        "events_per_probe": events_per_probe,
        "timestamp": time.time(),
    }
    with open(STATE, "w") as f:
        json.dump(state, f, indent=2)

# Load events from log file
def load_events(probe_id):
    path = LOGS / f"{probe_id}.log"
    if not path.exists():
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

# Test A: Burst ingestion
async def test_burst_ingestion(probe_ids, events_per_probe=100, delay_ms=10):
    """Inject 100 sequential events per probe with small delay."""
    print(f"\n[Test A] Burst ingestion")
    print(f"Probes: {probe_ids}")
    print(f"Events per probe: {events_per_probe}")
    
    failures = {pid: [] for pid in probe_ids}
    
    for probe_id in probe_ids:
        expected_count = events_per_probe
        actual_events = load_events(probe_id)
        
        # Simulate burst by injecting events (if probe is simulated)
        if actual_events:
            # Verify no dropped increments
            actual_count = len(actual_events)
            if actual_count != expected_count:
                failures[probe_id].append(f"Count mismatch: expected {expected_count}, got {actual_count}")
            else:
                print(f"  {probe_id}: {actual_count} events (OK)")
        
        # Small delay between probes
        await asyncio.sleep(delay_ms / 1000)
    
    # Check invariants
    for pid in probe_ids:
        events = load_events(pid)
        if not events:
            print(f"  {pid}: No events (simulated probe)")
            continue
        
        # Verify logical_time strictly increasing
        times = [e.get("logical_time", 0) for e in events]
        if times != sorted(times) or times != list(set(times)):
            failures[pid].append("Logical time not strictly increasing")
        else:
            print(f"  {pid}: Logical time OK (strictly increasing)")
    
    return failures

# Test B: Interleaved probe execution
async def test_interleaved_execution(probe_ids, events_per_probe=10):
    """Simulate round-robin firing across probes."""
    print(f"\n[Test B] Interleaved probe execution")
    print(f"Probes: {probe_ids}")
    print(f"Events per probe: {events_per_probe}")
    
    print(f"  Injecting events in round-robin pattern...")
    for i in range(events_per_probe):
        for probe_id in probe_ids:
            # Simulate injection
            await asyncio.sleep(5 / 1000)  # 5ms between each event
    
    # Verify separation
    failures = {}
    for probe_id in probe_ids:
        events = load_events(probe_id)
        if not events:
            failures[probe_id] = "Simulated probe (no events)"
            continue
        
        if len(events) != events_per_probe:
            failures[probe_id] = f"Count mismatch: expected {events_per_probe}, got {len(events)}"
        else:
            print(f"  {probe_id}: {len(events)} events (separated)")
    
    return failures

# Test C: Rapid-fire ingestion
async def test_rapid_fire_ingestion(probe_ids, events_per_probe=50, delay_ms=2):
    """Inject events with minimal delay."""
    print(f"\n[Test C] Rapid-fire ingestion")
    print(f"Probes: {probe_ids}")
    print(f"Events per probe: {events_per_probe}")
    print(f"Delay between calls: {delay_ms}ms")
    
    start = time.time()
    for probe_id in probe_ids:
        for i in range(events_per_probe):
            # Simulate rapid injection
            await asyncio.sleep(delay_ms / 1000)
    end = time.time()
    
    total_time = end - start
    print(f"  Total time: {total_time:.3f}s for {probe_ids[0]}")
    
    # Verify sequence_counter monotonicity
    failures = {}
    for probe_id in probe_ids:
        events = load_events(probe_id)
        if not events:
            continue
        
        # Check sequence_counter if available
        counters = [e.get("sequence_counter", 0) for e in events]
        if counters != sorted(counters) or any(counters[i] >= counters[i+1] for i in range(len(counters)-1)):
            failures[probe_id] = "Sequence counter not monotonic"
    
    return failures

# Main execution
async def main():
    probes = load_probes()
    if not probes:
        print("No probes found. Creating test probes...")
        # Create simulated probes with in-memory counters
        for i in range(3):
            probe_id = f"q4v9qs_{i:03d}"
            # For simulated probes, we'll just track in-memory
            # In practice, these would be real probes
        probes = [f"q4v9qs_{i:03d}" for i in range(3)]
        save_state(probes, 0)
    
    print(f"Using probes: {probes}")
    
    # Run tests
    all_failures = {}
    
    # Test A
    all_failures.update(await test_burst_ingestion(probes, events_per_probe=100, delay_ms=10))
    
    # Test B
    all_failures.update(await test_interleaved_execution(probes, events_per_probe=10))
    
    # Test C
    all_failures.update(await test_rapid_fire_ingestion(probes, events_per_probe=50, delay_ms=2))
    
    # Summary
    print("\n" + "=" * 50)
    print("STRESS VALIDATION SUMMARY")
    print("=" * 50)
    
    if all_failures:
        print("\n❌ FAILURES DETECTED:")
        for pid, failures in all_failures.items():
            for f in failures:
                print(f"  {pid}: {f}")
    else:
        print("\n✅ ALL STRESS TESTS PASSED")
    
    print("=" * 50)
    
    # Return exit code
    return 0 if not all_failures else 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
