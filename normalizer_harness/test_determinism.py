"""
test_determinism.py
Invariant: normalize(x) == normalize(x)

Binary enforcement only. No inference. No scoring.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from signal_normalizer import normalize


def test_determinism():
    """
    Determinism invariant:
    Same input must always produce same output.
    """
    # Test vector
    input_signal = {"latency_ms": 1837}
    
    # Run normalization multiple times
    result1 = normalize(input_signal)
    result2 = normalize(input_signal)
    result3 = normalize(input_signal)
    
    # Binary check: PASS or FAIL
    assert result1 == result2 == result3, "Determinism invariant violated"
    
    return "PASS" if result1 == result2 == result3 else "FAIL"


if __name__ == "__main__":
    result = test_determinism()
    print(f"test_determinism: {result}")
    sys.exit(0 if result == "PASS" else 1)
