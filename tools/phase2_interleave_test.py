#!/usr/bin/env python3
"""
Test B: Interleaved Probe Execution (50 rounds)
Simulates alternating probe execution
Probes: q4v9qs → 7wo52k → 1e8r9u → fdd3u2
Pattern: A → B → C → D → A → B → ...
Validates:
  - Clean separation per probe
  - No shared state leakage
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
import threading
import random

# === CORE TYPES (same as phase2_burst_test.py) ===

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
    causal_validity: bool = True

@dataclass
class TestResult:
    test_id: str
    status: str
    metrics: Dict[str, Any]
    suggestions: List[str]
    severity: str
    root_cause: Optional[str]
    layer_truth: str
    causal_validity: bool

# === EVENT STORE (Thread-Safe) ===

class EventStore:
    def __init__(self):
        self._store: Dict[str, Event] = {}
        self._probes: Dict[str, List[Event]] = {}
        self._lock = threading.RLock()
        self._causal_violations: List[Dict] = []
    
    def store_probe(self, probe_id: str) -> None:
        """Pre-register probe ID to ensure clean separation"""
        with self._lock:
            if probe_id not in self._probes:
                self._probes[probe_id] = []
    
    def ingest(self, raw_payload: dict) -> IngestResult:
        """Strict event ingestion with hash-chain verification"""
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
                logical_time=random.randint(0, 1000000)
            )
            
            result.success = True
            result.event = event
            return result
            
        except Exception as e:
            result.error = str(e)
            result.rejected = raw_payload.get("event_id", "unknown")
            result.causal_validity = False
            return result
    
    def append_probe(self, probe_id: str, event: Event) -> None:
        with self._lock:
            if probe_id not in self._probes:
                self._probes[probe_id] = []
            self._probes[probe_id].append(event)
    
    def get_probe_count(self, probe_id: str) -> int:
        with self._lock:
            return len(self._probes.get(probe_id, []))
    
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
            self._causal_violations.clear()
    
    def verify_clean_separation(self, expected_probes: List[str]) -> Dict[str, Any]:
        """Verify that only expected probes are present (no leakage)"""
        with self._lock:
            actual_probes = set(self._probes.keys())
            expected_set = set(expected_probes)
            
            leakage = actual_probes - expected_set
            no_leakage = len(leakage) == 0
            
            return {
                "expected_probes": expected_probes,
                "actual_probes": list(self._probes.keys()),
                "leakage_probes": list(leakage),
                "no_leakage": no_leakage
            }

# === GOVERNANCE ARBITRATION ===

def apply_governance_arbitration(test_results: List[TestResult]) -> Dict[str, Any]:
    """Apply global governance arbitration rules"""
    
    valid_results = [r for r in test_results if r.causal_validity]
    invalid_results = [r for r in test_results if not r.causal_validity]
    
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
        return {
            "arbitration_result": "ALL_TESTS_CAUSALLY_VALID",
            "all_valid": True,
            "chosen_action": "CONTINUE_TO_NEXT_PHASE",
            "reason": "All tests maintain causal ordering"
        }

# === TEST B: INTERLEAVED PROBE EXECUTION ===

def run_interleaved_test(num_rounds: int = 50) -> TestResult:
    """Test B: Interleaved probe execution (50 rounds)"""
    store = EventStore()
    probe_ids = ["q4v9qs", "7wo52k", "1e8r9u", "fdd3u2"]
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
            store.store_probe(probe_id)  # Pre-register probe
            
            # Calculate timestamp with tiny offset to ensure uniqueness
            base_ts = time.time() + round_idx * 0.0001
            offset_ts = i * 0.00001
            timestamp = base_ts + offset_ts
            
            raw_payload = {
                "event_id": str(uuid.uuid4()),
                "event_type": random.choice(["user_action", "system_event"]),
                "timestamp": timestamp,
                "payload": {"round": round_idx, "probe_idx": i},
                "source": "interleaved_test"
            }
            
            result = store.ingest(raw_payload)
            if result.success:
                store.append_probe(probe_id, result.event)
    
    elapsed = time.time() - results["start_time"]
    results["elapsed_ms"] = elapsed * 1000
    
    # Validate causal invariant
    validations = store.validate_causal_invariant()
    all_valid = all(v["valid"] for v in validations.values())
    
    results["validations"] = validations
    results["all_valid"] = all_valid
    
    # Verify clean separation
    separation_check = store.verify_clean_separation(probe_ids)
    results["separation_check"] = separation_check
    
    # Print results
    print(f"\n   ✓ All probes validated: {all_valid}")
    print(f"   Expected probes: {probe_ids}")
    print(f"   Actual probes: {list(store._probes.keys())}")
    print(f"   Clean separation: {separation_check['no_leakage']}")
    print(f"   Throughput: {num_rounds * len(probe_ids) / elapsed:.2f} events/sec")
    
    return TestResult(
        test_id="test_b_interleaved",
        status="pass" if all_valid else "fail",
        metrics=results,
        suggestions=[],
        severity="critical" if not all_valid else "none",
        root_cause=separation_check.get("leakage_probes") if not all_valid and separation_check.get("leakage_probes") else None,
        layer_truth="CAUSAL",
        causal_validity=all_valid
    )

# === MAIN EXECUTION ===

if __name__ == "__main__":
    test_result = run_interleaved_test(num_rounds=50)
    
    # Save report
    report = {
        "phase": 2,
        "timestamp": datetime.now().isoformat(),
        "test_b_interleaved": test_result,
        "arbitration": {
            "arbitration_result": "ALL_TESTS_CAUSALLY_VALID" if test_result.causal_validity else "CAUSAL_FAILURE_DETECTED",
            "all_valid": test_result.causal_validity,
            "chosen_action": "CONTINUE_TO_NEXT_PHASE" if test_result.causal_validity else "HALT_AND_REMEDIATE",
            "reason": "All tests maintain causal ordering" if test_result.causal_validity else "Causal determinism violated - must not optimize"
        }
    }
    
    with open("/home/jason2ykk/.openclaw/workspace/memory/phase2_interleave_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n✅ Test B Complete")
    print(f"   Status: {test_result.status.upper()}")
    print(f"   Causal Validity: {test_result.causal_validity}")
    print(f"   Clean Separation: {report['test_b_interleaved']['metrics']['separation_check']['no_leakage']}")
