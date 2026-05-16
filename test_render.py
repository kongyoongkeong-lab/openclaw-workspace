#!/usr/bin/env python3
"""Render regression test suite"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

# Mock imports
class MockStatus:
    def __init__(self, status):
        self.status = status
        self.warning = False
        self.invariant_break = False
        self.degradation = False
        self.user_decision = False

class MockEvent:
    def __init__(self, status, needs_awareness=False):
        self.status = status
        self.needs_awareness = needs_awareness

# Test Fix 1: progress exact one line
def test_progress_exact_one_line():
    print("Test 1: progress_exact_one_line")
    status = MockStatus("stable")
    result = render_progress(status.status, status.warning, status.invariant_break, status.degradation, status.user_decision)
    assert result == "Stable. No user action required.", f"Got: {result}"
    print("✅ PASS: Output: Stable. No user action required.")

# Test Fix 2: continue_runtime_event stable one line
def test_continue_runtime_event_stable_one_line():
    print("\nTest 2: continue_runtime_event_stable_one_line")
    event = MockEvent("stable")
    result = render_runtime_event(event)
    assert result == "Stable. No user action required.", f"Got: {result}"
    print("✅ PASS: Output: Stable. No user action required.")

# Test Fix 3: metric labels locked
def test_metric_names_locked():
    print("\nTest 3: metric_names_locked")
    assert format_metric("RPR", "0.09") == "RPR = 0.09"
    assert format_metric("GAF", "0.25") == "GAF = 0.25"
    print("✅ PASS: Metric names locked correctly.")

if __name__ == "__main__":
    from patch_render import render_progress, render_runtime_event, format_metric
    test_progress_exact_one_line()
    test_continue_runtime_event_stable_one_line()
    test_metric_names_locked()
    print("\n✅ All regression tests passed.")