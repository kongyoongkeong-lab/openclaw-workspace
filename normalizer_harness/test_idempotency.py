"""
test_idempotency.py
Invariant: normalize(normalize(x)) == normalize(x)

Binary enforcement only. No inference. No scoring.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from signal_normalizer import normalize


def test_idempotency():
    """
    Idempotency invariant:
    Double normalization must equal single normalization.
    """
    # Test vector
    input_signal = {"latency_ms": 1837}
    
    # Single normalization
    result1 = normalize(input_signal)
    
    # Double normalization
    result2 = normalize(result1)
    
    # Binary check: PASS or FAIL
    assert result1 == result2, "Idempotency invariant violated"
    
    return "PASS" if result1 == result2 else "FAIL"


if __name__ == "__main__":
    result = test_idempotency()
    print(f"test_idempotency: {result}")
    sys.exit(0 if result == "PASS" else 1)
