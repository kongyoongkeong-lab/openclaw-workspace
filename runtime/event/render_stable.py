"""
Stable Runtime Event Renderer v0.0.1
Pentagon Render Fix - Only renders "Stable. No user action required." when system is stable.
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

from runtime.render.render_policy import RenderPolicy

def render_progress() -> str:
    """
    Render progress command output.
    
    Expected exact output: "Stable. No user action required."
    
    No:
    - title
    - status line
    - output label
    - verification sentence
    - emojis
    - metrics
    - telemetry
    - protocol explanation
    """
    return RenderPolicy.render_progress()

def render_runtime_event_stable() -> str:
    """
    Render stable runtime event.
    
    Expected output: "Stable. No user action required."
    
    Only render event details if:
    - new state change requires user awareness
    - warning occurs
    - invariant breaks
    - degradation detected
    - user explicitly asks for full event details
    """
    return RenderPolicy.render_runtime_event_stable()

def render_full_telemetry() -> str:
    """
    Render full telemetry report on explicit request.
    
    Uses locked metric labels:
    - RPR = Retrieval Pollution Ratio
    - GAF = Governance Amplification Factor
    
    Never shows inconsistent target lines.
    """
    return RenderPolicy.render_full_telemetry()

if __name__ == "__main__":
    print("=== Pentagon Render Stable Fix v0.0.1 ===\n")
    
    # Test 1: progress
    print("Test 1: progress")
    result = render_progress()
    print(f"Output: {result!r}")
    print(f"Length: {len(result)}\n")
    
    # Test 2: continue_runtime_event (stable)
    print("Test 2: continue_runtime_event (stable)")
    result = render_runtime_event_stable()
    print(f"Output: {result!r}\n")
    
    # Test 3: full telemetry
    print("Test 3: full telemetry")
    result = render_full_telemetry()
    print(f"Output:\n{result}\n")
    
    print("=== All tests completed ===")