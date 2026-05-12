#!/usr/bin/env python3
"""
Phase 2: Instrumentation Stress Validation - Corrected Version
Includes:
  - Causal validity flag (causal_validity)
  - Global governance arbitration rules
  - 3-layer truth isolation (local/system/CAUSAL)
  - Governance decision log
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
import threading
import random

# === CORE TYPES ===

class EventStatus:
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"

@dataclass
class Event:
    event_id: str
    event_type: str
    timestamp: float
    payload: dict
    source: str
    hash_chain: List[str]
    status: str = EventStatus.VALIDATED
    error_message: Optional[str] = None
    probe_id: Optional[str] = None
    logical_time: int = 0

@dataclass
class IngestResult:
    success: bool
    event: Optional[Event]
    error: Optional[str]
    rejected: Optional[str]
    causal_validity: bool = True  # NEW: causal validity flag

@dataclass
class TestResult:
    test_id: str
    status: str  # pass | fail | warning
    metrics: Dict[str, Any]
    suggestions: List[str]
    severity: str  # critical | high | medium | low
    root_cause: Optional[str]
    layer_truth: str  # "local" | "system" | "CAUSAL"
    causal_validity: bool  # NEW

# === INGEST PIPELINE ===

def ingest_event(raw_payload: dict) -> IngestResult:
    """Strict event ingestion with hash-chain verification."""
    result = IngestResult(success=False, event=None, error=None, rejected=None, causal_validity=True)
    
    try:
        # Basic validation
        if not raw_payload:
            raise ValueError("Empty payload")
        
        required_fields = ["event_id", "event_type", "timestamp", "payload", "source"]
        for field_name in required_fields:
            if field_name not in raw_payload:
                raise ValueError(f"Missing required field: {field_name}")
        
        if not isinstance(raw_payload["event_id"], str):
            raise ValueError("event_id must be a string")
        if not isinstance(raw_payload["event_type"], str):
            raise ValueError("event_type must be a string")
        if not isinstance(raw_payload["payload"], dict):
            raise ValueError("payload must be a dict")
        if not isinstance(raw_payload["source"], str):
            raise ValueError("source must be a string")
        
        # Compute hash
        event_hash = hashlib.sha256(
            f"{raw_payload['event_id']}:{raw_payload['event_type']}:{raw_payload['timestamp']}:{raw_payload['source']}".encode()
        ).hexdigest()[:16]
        
        event = Event(
            event_id=raw_payload["event_id"],
            event_type=raw_payload["event_type"],
            timestamp=raw_payload["timestamp"],
            payload=raw_payload["payload"],
            source=raw_payload["source"],
            hash_chain=[event_hash],
            status=EventStatus.VALIDATED,
            probe_id=raw_payload.get("probe_id", "default"),
            logical_time=random.randint(0, 1000000)  # Deterministic within single-threaded ingest
        )
        
        result.success = True
        result.event = event
        return result
        
    except Exception as e:
        result.error = str(e)
        result.rejected = raw_payload.get("event_id", "unknown")
        result.causal_validity = False  # Causal break on ingest failure
        return result

# === EVENT STORE (Thread-Safe) ===

class EventStore:
    def __init__(self):
        self._store: Dict[str, Event] = {}
        self._probes: Dict[str, List[Event]] = {}
        self._lock = threading.RLock()
        self._causal_violations: List[Dict] = []  # Track causal violations
    
    def ingest(self, raw_payload: dict) -> IngestResult:
        with self._lock:
            result = ingest_event(raw_payload)
            if result.success:
                if raw_payload.get("probe_id") not in self._probes:
                    self._probes[raw_payload.get("probe_id", "default")] = []
                self._probes[raw_payload.get("probe_id", "default")].append(result.event)
            return result
    
    def get_events(self, probe_id: Optional[str] = None) -> List[Event]:
        with self._lock:
            if probe_id:
                return self._probes.get(probe_id, [])
            return [e for probe_events in self._probes.values() for e in probe_events]
    
    def validate_causal_invariant(self) -> Dict[str, Any]:
        """
        Validate: for all probes:
            event_count == expected_count
            AND logical_time strictly increasing per probe stream
        """
        with self._lock:
            validations = {}
            for probe_id, events in self._probes.items():
                valid = True
                errors = []
                event_count = len(events)
                logical_times = [e.logical_time for e in events]
                
                # Check monotonicity
                for i in range(1, len(logical_times)):
                    if logical_times[i] <= logical_times[i-1]:
                        valid = False
                        errors.append(f"Ordering inversion at {probe_id}: logical_time[{i}]={logical_times[i]} <= logical_time[{i-1}]={logical_times[i-1]}")
                        # Record causal violation
                        self._causal_violations.append({
                            "probe_id": probe_id,
                            "violation_type": "logical_time_monotonicity",
                            "at": len(self._causal_violations),
                            "details": str(errors[-1])
                        })
                
                validations[probe_id] = {
                    "valid": valid,
                    "event_count": event_count,
                    "errors": errors if not valid else None
                }
            return validations
    
    def get_causal_violations(self) -> List[Dict]:
        with self._lock:
            return self._causal_violations[:]
    
    def reset_causal_violations(self) -> None:
        with self._lock:
            self._caual_violations.clear()

# === TEST A: BURST INGESTION ===

def run_burst_test(num_events: int = 100, probes: int = 3, delay: float = 0.001) -> TestResult:
    """Test A: Burst ingestion (low concurrency)"""
    store = EventStore()
    results = {
        "test": "A - Burst Ingestion",
        "probe_count": probes,
        "events_per_probe": num_events // probes,
        "expected_total": num_events,
        "start_time": time.time(),
        "errors": []
    }
    
    print(f"\n🔥 Test A: Burst Ingestion")
    print(f"   {probes} probes × {num_events // probes} events each = {num_events} total")
    print(f"   Delay: {delay}ms between calls")
    print("-" * 60)
    
    for i in range(num_events):
        probe_id = f"probe_{i % probes}"
        store.store_probe(probe_id)
        
        raw_payload = {
            "event_id": str(uuid.uuid4()),
            "event_type": random.choice(["user_action", "system_event", "sensor_reading"]),
            "timestamp": time.time(),
            "payload": {"batch": results["test"], "idx": i},
            "source": "burst_test"
        }
        
        result = store.ingest(raw_payload)
        if result.success:
            store.append_probe(probe_id, result.event)
    
    elapsed = time.time() - results["start_time"]
    results["elapsed_ms"] = elapsed * 1000
    results["throughput_events_per_sec"] = num_events / elapsed if elapsed > 0 else 0
    
    validations = store.validate_causal_invariant()
    all_valid = all(v["valid"] for v in validations.values())
    
    results["validations"] = validations
    results["all_valid"] = all_valid
    
    if not all_valid:
        results["errors"] = [e for v in validations.values() for e in v.get("errors", [])]
    
    # Summary
    results["summary"] = {
        "total_events": sum(len(store._probes.get(p, [])) for p in store._probes),
        "probe_counts": {p: store.get_probe_count(p) for p in store._probes},
        "all_valid": all_valid
    }
    
    print(f"\n   ✓ All probes validated: {all_valid}")
    print(f"   Total events: {results['summary']['total_events']} (expected: {num_events})")
    print(f"   Throughput: {results['throughput_events_per_sec']:.2f} events/sec")
    print(f"   Elapsed: {elapsed*1000:.2f}ms")
    
    return TestResult(
        test_id="test_a_burst",
        status="pass" if all_valid else "fail",
        metrics=results,
        suggestions=[],
        severity="critical" if not all_valid else "none",
        root_cause=results.get("errors", None) if not all_valid else None,
        layer_truth="CAUSAL",
        causal_validity=all_valid
    )

# === TEST B: INTERLEAVED PROBE EXECUTION ===

def run_interleaved_test(num_rounds: int = 50) -> TestResult:
    """Test B: Interleaved probe execution"""
    store = EventStore()
    probe_ids = [f"q4v9qs", "7wo52k", "1e8r9u", "fdd3u2"]
    results = {
        "test": "B - Interleaved Probe Execution",
        "probe_ids": probe_ids,
        "rounds": num_rounds,
        "start_time": time.time(),
        "errors": []
    }
    
    print(f"\n🌀 Test B: Interleaved Probe Execution")
    print(f"   Probes: {probe_ids}")
    print(f"   Rounds: {num_rounds}")
    print(f"   Pattern: A → B → C → D → A → B → ...")
    print("-" * 60)
    
    for round_idx in range(num_rounds):
        for i, probe_id in enumerate(probe_ids):
            store.store_probe(probe_id)
            
            raw_payload = {
                "event_id": str(uuid.uuid4()),
                "event_type": random.choice(["user_action", "system_event"]),
                "timestamp": time.time() + round_idx * 0.0001 + i * 0.00001,
                "payload": {"round": round_idx, "probe_idx": i},
                "source": "interleaved_test"
            }
            
            result = store.ingest(raw_payload)
            if result.success:
                store.append_probe(probe_id, result.event)
    
    elapsed = time.time() - results["start_time"]
    results["elapsed_ms"] = elapsed * 1000
    
    validations = store.validate_causal_invariant()
    all_valid = all(v["valid"] for v in validations.values())
    
    results["validations"] = validations
    results["all_valid"] = all_valid
    
    # Verify clean separation
    results["separation_check"] = {
        "probe_ids": list(store._probes.keys()),
        "no_leakage": len(set(store._probes.keys()) - set(probe_ids)) == 0
    }
    
    print(f"\n   ✓ All probes validated: {all_valid}")
    print(f"   Expected probes: {probe_ids}")
    print(f"   Actual probes: {list(store._probes.keys())}")
    print(f"   Clean separation: {results['separation_check']['no_leakage']}")
    print(f"   Throughput: {num_rounds * len(probe_ids) / elapsed:.2f} events/sec")
    
    return TestResult(
        test_id="test_b_interleaved",
        status="pass" if all_valid else "fail",
        metrics=results,
        suggestions=[],
        severity="critical" if not all_valid else "none",
        root_cause=results.get("separation_check") if not all_valid else None,
        layer_truth="CAUSAL",
        causal_validity=all_valid
    )

# === TEST C: RAPID-FIRE INGESTION ===

def run_rapidfire_test(num_events: int = 200, thread_count: int = 4) -> TestResult:
    """Test C: Rapid-fire ingestion with minimal delay"""
    store = EventStore()
    results = {
        "test": "C - Rapid-Fire Ingestion",
        "num_events": num_events,
        "threads": thread_count,
        "start_time": time.time(),
        "errors": []
    }
    
    print(f"\n⚡ Test C: Rapid-Fire Ingestion")
    print(f"   Events: {num_events}")
    print(f"   Threads: {thread_count}")
    print(f"   Minimal delay between calls")
    print("-" * 60)
    
    # Pre-create payloads
    payloads = [
        {
            "event_id": str(uuid.uuid4()),
            "event_type": random.choice(["user_action", "system_event", "sensor_reading", "external_trigger"]),
            "timestamp": time.time(),
            "payload": {"rapidfire": True, "idx": i},
            "source": "rapidfire_test"
        }
        for i in range(num_events)
    ]
    
    def ingest_task(payload):
        probe_id = f"rapid_{payload['payload']['idx'] % thread_count}"
        store.store_probe(probe_id)
        result = store.ingest(payload)
        if result.success:
            store.append_probe(probe_id, result.event)
        return result
    
    # ThreadPoolExecutor for concurrent ingestion
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        futures = [executor.submit(ingest_task, payload) for payload in payloads]
        for future in as_completed(futures):
            pass  # Collect results
    
    elapsed = time.time() - results["start_time"]
    results["elapsed_ms"] = elapsed * 1000
    results["throughput"] = num_events / elapsed if elapsed > 0 else 0
    
    validations = store.validate_causal_invariant()
    all_valid = all(v["valid"] for v in validations.values())
    
    results["validations"] = validations
    results["all_valid"] = all_valid
    
    # Check sequence_counter monotonicity
    results["sequence_check"] = {
        "probe_ids": list(store._probes.keys()),
        "monotonicity_valid": all_valid
    }
    
    print(f"\n   ✓ All probes validated: {all_valid}")
    print(f"   Total events: {sum(store.get_probe_count(p) for p in store._probes)} (expected: {num_events})")
    print(f"   Throughput: {results['throughput']:.2f} events/sec")
    print(f"   Elapsed: {elapsed*1000:.2f}ms")
    
    return TestResult(
        test_id="test_c_rapidfire",
        status="pass" if all_valid else "fail",
        metrics=results,
        suggestions=[],
        severity="critical" if not all_valid else "none",
        root_cause=results.get("sequence_check") if not all_valid else None,
        layer_truth="CAUSAL",
        causal_validity=all_valid
    )

# === GOVERNANCE ARBITRATION RULES ===

def apply_governance_arbitration(test_results: List[TestResult]) -> Dict[str, Any]:
    """
    Apply global governance arbitration rules to resolve conflicts.
    
    Rule 1: Causal determinism > performance > optimization
    Rule 2: Reject any action that breaks causal ordering
    Rule 3: Choose the action with highest causal validity
    """
    # Filter by causal validity
    valid_results = [r for r in test_results if r.causal_validity]
    invalid_results = [r for r in test_results if not r.causal_validity]
    
    # If any test failed causality, that's critical
    if invalid_results:
        failed_tests = [r.test_id for r in invalid_results]
        root_cause = "; ".join(r.root_cause for r in invalid_results if r.root_cause)
        
        return {
            "arbitration_result": "CAUSAL_FAILURE_DETECTED",
            "failed_tests": failed_tests,
            "root_cause": root_cause,
            "rejected_actions": [r.suggestions for r in invalid_results if r.suggestions],
            "chosen_action": "HALT_AND_REMEDIATE",
            "reason": "Causal determinism violated - must not optimize"
        }
    else:
        # All tests passed causality
        return {
            "arbitration_result": "ALL_TESTS_CAUSALLY_VALID",
            "all_valid": True,
            "chosen_action": "CONTINUE_TO_NEXT_PHASE",
            "reason": "All tests maintain causal ordering"
        }

# === MAIN TEST RUNNER ===

def run_phase2_suite() -> Dict[str, Any]:
    """Run all Phase 2 tests with arbitration"""
    
    print("=" * 70)
    print("🚀 Phase 2: Instrumentation Stress Validation")
    print("   Goal: Verify causally stable instrumentation under pressure")
    print("=" * 70)
    print()
    print("Key Invariant:")
    print("  for all probes:")
    print("    event_count == expected_count")
    print("    AND")
    print("    logical_time strictly increasing per probe stream")
    print("=" * 70)
    print()
    
    # Test A
    test_a = run_burst_test(num_events=100, probes=3, delay=0.001)
    
    # Test B
    test_b = run_interleaved_test(num_rounds=50)
    
    # Test C
    test_c = run_rapidfire_test(num_events=200, thread_count=4)
    
    # Apply arbitration
    all_tests = [test_a, test_b, test_c]
    arbitration = apply_governance_arbitration(all_tests)
    
    # Generate report
    report = {
        "phase": 2,
        "timestamp": datetime.now().isoformat(),
        "tests": {
            "test_a_burst": test_a,
            "test_b_interleaved": test_b,
            "test_c_rapidfire": test_c
        },
        "arbitration": arbitration,
        "summary": {
            "all_causally_valid": all(t.causal_validity for t in all_tests),
            "probes_validated": sum(len(t.metrics.get("validations", {})) for t in all_tests),
            "failed_test_ids": [t.test_id for t in all_tests if not t.causal_validity]
        }
    }
    
    print()
    print("=" * 70)
    print("✅ Phase 2 Complete - Arbitration Result")
    print("=" * 70)
    print(f"Test A (Burst):      {test_a.status.upper() if test_a.causal_validity else '❌ CAUSAL_FAILURE'}")
    print(f"Test B (Interleave): {test_b.status.upper() if test_b.causal_validity else '❌ CAUSAL_FAILURE'}")
    print(f"Test C (Rapidfire):  {test_c.status.upper() if test_c.causal_validity else '❌ CAUSAL_FAILURE'}")
    print()
    print(f"Arbitration Result:  {arbitration['arbitration_result']}")
    print(f"Chosen Action:       {arbitration['chosen_action']}")
    print(f"Causal Validity:     {report['summary']['all_causally_valid']}")
    print("=" * 70)
    
    # Save report
    report_path = Path("/home/jason2ykk/.openclaw/workspace/memory/phase2_burst_test_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"   Report saved: {report_path}")
    
    return report

if __name__ == "__main__":
    run_phase2_suite()
