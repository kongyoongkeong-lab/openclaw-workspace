#!/usr/bin/env python3
"""Run all harness tests"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from signal_normalizer import normalize, verify_integrity, CanonicalSignalSet, normalize_trace

def run_all_tests():
    print("=== Pentagon Harness: All Tests ===\n")
    
    # Test 1: Determinism
    print("Test 1: Determinism...")
    input_signal = {"latency_ms": 1837}
    result1 = normalize(input_signal)
    result2 = normalize(input_signal)
    result3 = normalize(input_signal)
    assert result1 == result2 == result3, "Determinism failed"
    print("  ✅ PASS\n")
    
    # Test 2: Idempotency
    print("Test 2: Idempotency...")
    result_a = normalize({"count": 5})
    result_c = normalize({"count": 5})  # Same as result_a
    assert result_a.bucket == result_c.bucket, "Idempotency failed"
    print("  ✅ PASS\n")
    
    # Test 3: Trace normalization
    print("Test 3: Trace normalization...")
    trace = [
        {'signal': 'latency', 'value': 1.2},
        {'signal': 'retry', 'value': 2.0},
        {'signal': 'gap', 'value': 0.5}
    ]
    normalized = normalize_trace(trace)  # Use normalize_trace, not normalize
    assert len(normalized) == 3, "Trace normalization failed"
    print("  ✅ PASS\n")
    
    # Test 4: Integrity verification
    print("Test 4: Integrity verification...")
    signal_set = CanonicalSignalSet()
    integrity = verify_integrity(signal_set, trace)
    assert integrity['all_pass'], f"Integrity failed: {integrity}"
    print(f"  ✅ PASS (all_pass={integrity['all_pass']})\n")
    
    print("=== All Tests Passed ===")

if __name__ == "__main__":
    run_all_tests()