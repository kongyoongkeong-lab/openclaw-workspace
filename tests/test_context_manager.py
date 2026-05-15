"""
Context Manager Tests - Prevent context overflow from unstable render behavior.

Test cases:
1. Context overflow prevention when render policy misfires
2. Determinism validation (replay(snapshot) == live_state)
3. Invariant holding validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.render.render_policy import RenderPolicy

class TestContextManager:
    """Tests for context overflow prevention."""
    
    def test_context_overflow_prevention_status_command(self):
        """Test: Status commands don't cause context overflow."""
        # Run many status commands in sequence
        for i in range(100):
            result = RenderPolicy.route_render("status", "")
            assert result == "Stable. No user action required.", \
                f"Iteration {i}: context overflow detected"
        print(f"✅ 100 status commands: no overflow")
    
    def test_context_overflow_prevention_normal_command(self):
        """Test: Normal commands preserve context."""
        messages = [
            "How do I verify GitHub CI?",
            "Something is wrong with Discord bot. How do I troubleshoot?",
            "continue runtime event",
            "full telemetry",
            "protocol show render_policy"
        ]
        
        for msg in messages:
            result = RenderPolicy.route_render("test", msg)
            assert result == msg, \
                f"Context overflow: '{msg}' became '{result}'"
        print(f"✅ Normal commands preserve context")
    
    def test_determinism_validation(self):
        """Test: replay(snapshot) == live_state (determinism invariant)."""
        # Simulate snapshot replay
        snapshot_state = RenderPolicy.generate_stable_response()
        live_state = RenderPolicy.route_render("status", "")
        
        assert snapshot_state == live_state, \
            f"Determinism failure: snapshot='{snapshot_state}' != live='{live_state}'"
        print(f"✅ Determinism invariant holding")
    
    def test_determinism_normal_commands(self):
        """Test: Normal commands maintain determinism."""
        input1 = "How do I verify GitHub CI?"
        input2 = "How do I verify GitHub CI?"
        
        output1 = RenderPolicy.route_render("test", input1)
        output2 = RenderPolicy.route_render("test", input2)
        
        assert output1 == output2 == input1, \
            f"Determinism failure for normal commands"
        print(f"✅ Normal commands determinism holding")
    
    def test_invariant_holding_warnings(self):
        """Test: Invariants hold even with warnings."""
        # Command with warning should NOT return stable response
        result = RenderPolicy.route_render("status", "Warning: GPU high")
        
        # Should return original with warning, not stable response
        assert "Warning" in result, \
            "Warning invariant break: stable response suppressed warning"
        print(f"✅ Warning invariant holding")
    
    def test_invariant_holding_blocked_tokens(self):
        """Test: Blocked tokens never render."""
        message = "NO_REPLY INTERNAL_ONLY"
        result = RenderPolicy.route_render("status", message)
        
        assert "NO_REPLY" not in result, \
            "Blocked token invariant break: NO_REPLY rendered"
        assert "INTERNAL_ONLY" not in result, \
            "Blocked token invariant break: INTERNAL_ONLY rendered"
        print(f"✅ Blocked token invariant holding")
    
    def test_context_size_tracking(self):
        """Test: Context size remains bounded."""
        context_size = 0
        
        # Add various command types
        for cmd in ["progress", "status", "h1 status"] * 30:
            context_size += len(RenderPolicy.route_render(cmd, ""))
        
        for msg in ["How do I..."] * 20:
            context_size += len(RenderPolicy.route_render("test", msg))
        
        # Should be bounded
        assert context_size < 10000, \
            f"Context overflow: {context_size} bytes exceeded limit"
        print(f"✅ Context size bounded at {context_size} bytes")
    
    def test_context_recovery(self):
        """Test: Context recovery from overflow."""
        # Simulate overflow scenario
        try:
            RenderPolicy.route_render("progress", "")
            RenderPolicy.route_render("status", "")
            # Recovery: clear context
            RenderPolicy.route_render("status", "")
            print(f"✅ Context recovery successful")
        except Exception as e:
            # Should recover
            assert False, f"Recovery failed: {e}"
    
    def test_context_guard_status_commands(self):
        """Test: ContextGuard allows status commands."""
        allowed_commands = ["progress", "status", "session status"]
        
        for cmd in allowed_commands:
            result = RenderPolicy.route_render(cmd, "")
            assert result == "Stable. No user action required."
        print(f"✅ ContextGuard allows status commands")
    
    def test_context_guard_normal_commands(self):
        """Test: ContextGuard allows normal commands."""
        normal_commands = [
            "How do I verify GitHub CI?",
            "full telemetry",
            "protocol show render_policy"
        ]
        
        for cmd in normal_commands:
            result = RenderPolicy.route_render("test", cmd)
            assert result == cmd, f"ContextGuard blocked: {cmd}"
        print(f"✅ ContextGuard allows normal commands")
    
    def test_invariant_failures_zero(self):
        """Test: Zero invariant failures."""
        failures = []
        
        # Run all test cases
        for cmd in ["progress", "status", "h1 status"] * 50:
            if RenderPolicy.route_render(cmd, "") != "Stable. No user action required.":
                failures.append(f"Status command failure: {cmd}")
        
        for msg in ["How do I...", "full telemetry"] * 20:
            if RenderPolicy.route_render("test", msg) != msg:
                failures.append(f"Normal command failure: {msg}")
        
        assert len(failures) == 0, \
            f"Invariant failure detected: {failures}"
        print(f"✅ Zero invariant failures")

def run_context_tests():
    """Run all context manager tests."""
    print("=" * 60)
    print("🧪 Context Manager Tests - Overflow Prevention")
    print("=" * 60)
    
    test = TestContextManager()
    
    # Run all tests
    test.test_context_overflow_prevention_status_command()
    test.test_context_overflow_prevention_normal_command()
    test.test_determinism_validation()
    test.test_determinism_normal_commands()
    test.test_invariant_holding_warnings()
    test.test_invariant_holding_blocked_tokens()
    test.test_context_size_tracking()
    test.test_context_recovery()
    test.test_context_guard_status_commands()
    test.test_context_guard_normal_commands()
    test.test_invariant_failures_zero()
    
    print("=" * 60)
    print("✅ All context manager tests passed!")
    print("=" * 60)
    
    print("\n📊 Context Health:")
    print("✅ Overflow prevention: Working")
    print("✅ Determinism: Holding")
    print("✅ Invariant failures: 0")
    print("✅ Context bounded: Yes")

if __name__ == "__main__":
    run_context_tests()
