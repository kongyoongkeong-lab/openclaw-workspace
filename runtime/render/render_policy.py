"""
Render Policy - Command-Aware Routing
Enforces stable response only for status-only commands when no warnings/failures present.
"""

import re
from typing import Tuple, Optional

# Status-only commands that trigger stable response
STATUS_COMMANDS = frozenset([
    'progress', 'status', 'h1 status', 
    'quiet soak status', 'session status'
])

# Blocked tokens that must never render
BLOCKED_TOKENS = frozenset([
    'NO_REPLY', 'INTERNAL_ONLY', 'CONTROL_ONLY', 'SYSTEM_ONLY'
])

class RenderPolicy:
    """Enforces command-aware render policy to prevent context overflow."""
    
    @classmethod
    def _has_warning_failure_degradation(cls, message: str) -> bool:
        """
        Detect only actual warning/failure/degradation signals.

        This intentionally avoids treating stable phrases like
        "no invariant break" as an invariant break.
        """
        text = message.lower() if message else ''

        negative_invariant_phrases = (
            'no invariant break',
            'no invariant breaks',
            'invariant break: no',
            'invariant break: false',
            'invariant_break: false',
        )
        if any(phrase in text for phrase in negative_invariant_phrases):
            text = text.replace('no invariant breaks', '')
            text = text.replace('no invariant break', '')
            text = text.replace('invariant break: no', '')
            text = text.replace('invariant break: false', '')
            text = text.replace('invariant_break: false', '')

        signal_patterns = (
            'warning', 'failure', 'failed', 'error', 'degraded', 'degradation',
            'invariant break', 'invariant_break', 'violation', 'critical',
            'unstable', 'alert', 'exception'
        )
        return any(pattern in text for pattern in signal_patterns)
    
    @classmethod
    def should_apply_stable_response(cls, command: str, message: str) -> bool:
        """
        Determine if stable response should be applied.
        
        Stable response is ONLY applied when:
        1. Command is a status-only command (progress, status, etc.)
        2. No warnings/failures/degradations present
        3. No invariant breaks
        4. No user decision required
        """
        cmd_lower = command.lower().strip() if command else ''
        
        # Check if it's a status-only command
        if cmd_lower not in STATUS_COMMANDS:
            # Normal commands (questions, troubleshooting, etc.) -> NO stable response
            return False
        
        # Check for warnings/failures/degradations/invariant breaks in message.
        if cls._has_warning_failure_degradation(message):
            return False
        
        # Check for blocked tokens
        for token in BLOCKED_TOKENS:
            if token in message:
                return False
        
        # Check for user decision required
        if any(pattern in message.lower() for pattern in [
            'need your input', 'decide', 'confirm', 'approve',
            'user choice', 'manual review', 'awaiting confirmation'
        ]):
            return False
        
        return True
    
    @classmethod
    def render_progress(cls) -> str:
        """
        Render stable response for progress command.
        
        Expected exact output: "Stable. No user action required."
        (32 chars)
        
        No telemetry table. No metrics. No system state.
        Only for when: command == "progress" AND no warning 
        AND no failure AND no degradation AND no invariant break
        AND no user decision required
        """
        return "Stable. No user action required."
    
    @classmethod
    def generate_stable_response(cls, original: Optional[str] = None) -> str:
        """
        Generate the exact stable response string.
        
        Expected exact: "Stable. No user action required."
        (Length: 32 chars)
        """
        return "Stable. No user action required."  # 32 chars exactly (matches requirement)
    
    @classmethod
    def format_telemetry_metric(cls, name: str, value: str) -> str:
        """
        Format telemetry metric with locked labels.
        
        Always use:
        RPR = Retrieval Pollution Ratio
        GAF = Governance Amplification Factor
        
        Never show inconsistent target lines like "Target <0.10" when GAF 0.25 is stable.
        """
        # Locked label names only
        labels = {
            "RPR": "Retrieval Pollution Ratio",
            "GAF": "Governance Amplification Factor"
        }
        # Simple value format, no inconsistent target lines
        return f"{name} = {value}"
    
    @classmethod
    def render_full_telemetry(cls, payload: Optional[str] = None) -> str:
        """
        Render full telemetry report on explicit request.
        
        Only include:
        - Current metric values with locked labels
        - Hardware status (GPU, VRAM)
        - System health indicators
        
        Never include inconsistent GAF target lines when policy treats current value as stable.
        """
        # Preserve supplied telemetry. Do not invent/fabricate missing values.
        if payload:
            return cls.strip_blocked_tokens(payload)
        return ""
    
    @classmethod
    def render_runtime_event_stable(cls) -> str:
        """
        Render stable runtime event (no details).
        
        Only render details if:
        - new state change requires user awareness
        - warning occurs
        - invariant breaks
        - degradation detected
        - user explicitly asks for full event details
        """
        return "Stable. No user action required."
    
    @classmethod
    def is_stable_event(cls, event_data: dict) -> bool:
        """Check if event is stable (no user action needed)."""
        return (event_data.get("status") == "stable" and 
                not event_data.get("needs_awareness", False) and
                not event_data.get("warning", False))
    
    @classmethod
    def strip_blocked_tokens(cls, text: str) -> str:
        """
        Remove blocked tokens from text before rendering.
        Applied as final output step.
        """
        for token in BLOCKED_TOKENS:
            text = text.replace(token, '')
        return text.strip()
    
    @classmethod
    def route_render(cls, command: str, message: str) -> str:
        """
        Main routing logic for render decision.
        
        Returns:
            - Stable response for status-only + clean commands
            - Full telemetry for explicit requests (e.g., 'show full telemetry')
            - Normal response for all other cases (including non-status commands)
            - Empty string only if blocked tokens present
        """
        cmd_lower = command.lower().strip() if command else ''
        if cmd_lower == 'progress':
            if cls.should_apply_stable_response(command, message):
                return cls.render_progress()
            return cls.strip_blocked_tokens(message) if message else ""
        
        # Continue runtime event with stable status
        cmd_contain_continue = 'continue the openclaw runtime event' in cmd_lower
        if cmd_contain_continue:
            return cls.render_runtime_event_stable()
        
        # Check for explicit full-status requests only.
        if cmd_lower == 'show full telemetry':
            return cls.render_full_telemetry(message)

        if cmd_lower == 'show full protocol' or cmd_lower.startswith('protocol show '):
            return cls.strip_blocked_tokens(message) if message else ""
        
        # Status-only commands that trigger stable response
        if cmd_lower in STATUS_COMMANDS:
            if cls.should_apply_stable_response(command, message):
                return cls.generate_stable_response()
            else:
                # Return original message if not stable
                return cls.strip_blocked_tokens(message) if message else ""
        
        # Non-status commands: return original message (strip blocked tokens)
        # If message is empty, use command as message (or return empty if command also empty)
        if not message:
            return cls.strip_blocked_tokens(command) if command else ""
        
        return cls.strip_blocked_tokens(message)
    
    @classmethod
    def is_status_command(cls, command: str) -> bool:
        """Check if command is a status-only command."""
        cmd_lower = command.lower().strip() if command else ''
        return cmd_lower in STATUS_COMMANDS
    
    @classmethod
    def needs_stable_response(cls, command: str, message: str) -> Tuple[bool, str]:
        """
        Check if stable response needed and why.
        
        Returns:
            Tuple of (is_stable, reason)
        """
        if not cls.should_apply_stable_response(command, message):
            reason = "Command not in status-only set or contains warnings/failures"
            return False, reason
        
        reason = "Status-only command with no warnings/failures"
        return True, reason
