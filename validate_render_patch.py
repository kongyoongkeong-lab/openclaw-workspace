#!/usr/bin/env python3
"""Render patch validation suite"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

from runtime.render.render_policy import RenderPolicy

def run_tests():
    print("=== Pentagon Render Patch Validation ===\n")
    
    # Test 1: progress_exact_one_line
    print("1. progress_exact_one_line")
    result = RenderPolicy.render_progress()
    expected = "Stable. No user action required."
    assert result == expected, f"FAIL: Got {result!r}, expected {expected!r}"
    print(f"   ✅ PASS: {result}")
    print(f"   Length: {len(result)}")
    
    # Test 2: continue_runtime_event_stable_one_line
    print("\n2. continue_runtime_event_stable_one_line")
    result = RenderPolicy.render_runtime_event_stable()
    assert result == expected, f"FAIL: Got {result!r}, expected {expected!r}"
    print(f"   ✅ PASS: {result}")
    
    # Test 3: progress_no_header_no_emoji
    print("\n3. progress_no_header_no_emoji")
    assert "🚀" not in result and "🤖" not in result
    print(f"   ✅ PASS: No emojis found")
    
    # Test 4: progress_no_status_label
    print("\n4. progress_no_status_label")
    assert "status" not in result.lower()
    print(f"   ✅ PASS: No status label")
    
    # Test 5: metric_names_locked
    print("\n5. metric_names_locked")
    rpr = RenderPolicy.format_telemetry_metric("RPR", "0.09")
    gaf = RenderPolicy.format_telemetry_metric("GAF", "0.25")
    assert rpr == "RPR = 0.09"
    assert gaf == "GAF = 0.25"
    print(f"   ✅ RPR = {rpr}")
    print(f"   ✅ GAF = {gaf}")
    
    # Test 6: full_telemetry_allowed_on_explicit_request
    print("\n6. full_telemetry_allowed_on_explicit_request")
    full = RenderPolicy.render_full_telemetry()
    assert "🚀" in full and "H1 Metrics" in full
    print(f"   ✅ Full telemetry rendered correctly")
    
    # Test 7: blocked_tokens_never_render
    print("\n7. blocked_tokens_never_render")
    blocked = RenderPolicy.strip_blocked_tokens("Test NO_REPLY message")
    assert "NO_REPLY" not in blocked
    print(f"   ✅ Blocked tokens stripped")
    
    print("\n=== All 7 regression tests passed ===")
    return True

if __name__ == "__main__":
    try:
        run_tests()
        print("\n🚀 **Render Patch Validation Complete** 🤖")
    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        raise
