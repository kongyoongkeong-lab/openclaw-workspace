"""
Regression tests for render policy command-aware behavior.

Test cases:
1. progress returns exactly: "Stable. No user action required."
2. status returns exactly: "Stable. No user action required."
3. normal question is not suppressed with stable response
4. troubleshooting request is not suppressed
5. continue runtime event is not suppressed unless explicitly status-only
6. full telemetry command works (not suppressed)
7. protocol show render_policy works (not suppressed)
8. blocked tokens never render
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.render.render_policy import RenderPolicy

class TestRenderPolicy:
    """Regression tests for command-aware render policy."""
    
    def test_progress_returns_stable_response(self):
        """Test: progress returns exactly 'Stable. No user action required.'"""
        result = RenderPolicy.route_render("progress", "")
        expected = "Stable. No user action required."
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"✅ progress returns: {result}")
    
    def test_status_returns_stable_response(self):
        """Test: status returns exactly 'Stable. No user action required.'"""
        result = RenderPolicy.route_render("status", "")
        expected = "Stable. No user action required."
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"✅ status returns: {result}")
    
    def test_h1_status_returns_stable_response(self):
        """Test: h1 status returns exactly 'Stable. No user action required.'"""
        result = RenderPolicy.route_render("h1 status", "")
        expected = "Stable. No user action required."
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"✅ h1 status returns: {result}")
    
    def test_quiet_soak_status_returns_stable_response(self):
        """Test: quiet soak status returns exactly 'Stable. No user action required.'"""
        result = RenderPolicy.route_render("quiet soak status", "")
        expected = "Stable. No user action required."
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"✅ quiet soak status returns: {result}")
    
    def test_session_status_returns_stable_response(self):
        """Test: session status returns exactly 'Stable. No user action required.'"""
        result = RenderPolicy.route_render("session status", "")
        expected = "Stable. No user action required."
        assert result == expected, f"Expected '{expected}', got '{result}'"
        print(f"✅ session status returns: {result}")
    
    def test_normal_question_not_suppressed(self):
        """Test: Normal question is NOT suppressed with stable response."""
        command = "How do I verify GitHub CI?"
        message = "To verify GitHub CI, run: openclaw verify github"
        result = RenderPolicy.route_render(command, message)
        # Should return original message, NOT stable response
        assert result == message, f"Expected original message, got '{result}'"
        assert result != RenderPolicy.generate_stable_response(), "Normal question should not be suppressed"
        print(f"✅ Normal question returns: {result[:50]}...")
    
    def test_troubleshooting_request_not_suppressed(self):
        """Test: Troubleshooting request is NOT suppressed with stable response."""
        command = "Something is wrong with Discord bot. How do I troubleshoot?"
        result = RenderPolicy.route_render(command, "")
        expected = "Something is wrong with Discord bot. How do I troubleshoot?"
        assert result == expected, f"Expected original question, got '{result}'"
        assert result != RenderPolicy.generate_stable_response(), "Troubleshooting should not be suppressed"
        print(f"✅ Troubleshooting request returns: {result}")
    
    def test_continue_runtime_not_suppressed(self):
        """Test: Continue runtime event is NOT suppressed unless explicitly status-only."""
        command = "continue runtime event"
        result = RenderPolicy.route_render(command, "")
        expected = "continue runtime event"
        assert result == expected, f"Expected original command, got '{result}'"
        assert result != RenderPolicy.generate_stable_response(), "Continue runtime should not be suppressed"
        print(f"✅ Continue runtime returns: {result}")
    
    def test_full_telemetry_not_suppressed(self):
        """Test: Full telemetry command is NOT suppressed."""
        command = "full telemetry"
        message = "GPU: 74% | VRAM: 69% | Invariants: HOLDING | 🚀 System Stable 🤖"
        result = RenderPolicy.route_render(command, message)
        # Should return full telemetry, NOT stable response
        assert "GPU: 74%" in result or result == message, f"Full telemetry should be preserved, got '{result}'"
        assert result != RenderPolicy.generate_stable_response(), "Full telemetry should not be suppressed"
        print(f"✅ Full telemetry returns (not suppressed)")
    
    def test_protocol_show_not_suppressed(self):
        """Test: Protocol show command is NOT suppressed."""
        command = "protocol show render_policy"
        result = RenderPolicy.route_render(command, "Protocol details here...")
        assert result != RenderPolicy.generate_stable_response(), "Protocol show should not be suppressed"
        print(f"✅ Protocol show returns (not suppressed)")
    
    def test_blocked_tokens_strip(self):
        """Test: Blocked tokens are stripped from output."""
        message = "NO_REPLY INTERNAL_ONLY CONTROL_ONLY SYSTEM_ONLY Normal text"
        result = RenderPolicy.strip_blocked_tokens(message)
        # Should only contain "Normal text"
        assert "NO_REPLY" not in result, "NO_REPLY should be stripped"
        assert "INTERNAL_ONLY" not in result, "INTERNAL_ONLY should be stripped"
        assert "CONTROL_ONLY" not in result, "CONTROL_ONLY should be stripped"
        assert "SYSTEM_ONLY" not in result, "SYSTEM_ONLY should be stripped"
        assert "Normal text" in result, "Normal text should remain"
        print(f"✅ Blocked tokens stripped: '{result}'")
    
    def test_stable_response_exact_string(self):
        """Test: Stable response is exactly 'Stable. No user action required.'"""
        expected = "Stable. No user action required."
        result = RenderPolicy.generate_stable_response()
        assert result == expected, f"Expected '{expected}', got '{result}'"
        assert len(result) == 32, f"Length should be 32, got {len(result)}"
        print(f"✅ Stable response exact string: '{result}'")
    
    def test_status_command_detection(self):
        """Test: Status command detection works correctly."""
        assert RenderPolicy.is_status_command("progress") == True
        assert RenderPolicy.is_status_command("status") == True
        assert RenderPolicy.is_status_command("h1 status") == True
        assert RenderPolicy.is_status_command("full telemetry") == False
        assert RenderPolicy.is_status_command("How do I...") == False
        print(f"✅ Status command detection works")
    
    def test_reasoning_for_stable_response(self):
        """Test: Reasoning for when stable response is applied."""
        is_stable, reason = RenderPolicy.needs_stable_response("progress", "")
        assert is_stable == True, "Should need stable response for progress"
        assert "Status-only command" in reason, "Reason should mention status-only"
        print(f"✅ Stable response reasoning: {reason}")
        
        is_stable, reason = RenderPolicy.needs_stable_response("status", "Warning: GPU high")
        assert is_stable == False, "Should NOT need stable response when warning present"
        print(f"✅ Stable response blocked for warnings: {reason}")

def run_all_tests():
    """Run all regression tests."""
    print("=" * 60)
    print("🧪 Render Policy Regression Tests")
    print("=" * 60)
    
    test = TestRenderPolicy()
    
    # Run all test methods
    test.test_progress_returns_stable_response()
    test.test_status_returns_stable_response()
    test.test_h1_status_returns_stable_response()
    test.test_quiet_soak_status_returns_stable_response()
    test.test_session_status_returns_stable_response()
    test.test_normal_question_not_suppressed()
    test.test_troubleshooting_request_not_suppressed()
    test.test_continue_runtime_not_suppressed()
    test.test_full_telemetry_not_suppressed()
    test.test_protocol_show_not_suppressed()
    test.test_blocked_tokens_strip()
    test.test_stable_response_exact_string()
    test.test_status_command_detection()
    test.test_reasoning_for_stable_response()
    
    print("=" * 60)
    print("✅ All regression tests passed!")
    print("=" * 60)
    
    # Summary
    print("\n📊 Test Summary:")
    print("✅ progress -> 'Stable. No user action required.'")
    print("✅ status -> 'Stable. No user action required.'")
    print("✅ Normal questions -> NOT suppressed")
    print("✅ Troubleshooting -> NOT suppressed")
    print("✅ Continue runtime -> NOT suppressed")
    print("✅ Full telemetry -> NOT suppressed")
    print("✅ Protocol show -> NOT suppressed")
    print("✅ Blocked tokens -> Stripped")

if __name__ == "__main__":
    run_all_tests()
