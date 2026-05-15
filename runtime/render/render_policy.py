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
        
        # Check for warnings/failures/invariant breaks in message
        if any(pattern in message.lower() for pattern in [
            'warning', 'failure', 'error', 'degraded', 
            'break', 'violation', 'critical', 'unstable',
            'block', 'alert', 'exception'
        ]):
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
    def generate_stable_response(cls, original: Optional[str] = None) -> str:
        """
        Generate the exact stable response string.
        
        Expected exact: "Stable. No user action required."
        (Length: 30 chars for test compatibility)
        """
        return "Stable. No user action required."  # 30 chars exactly
    
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
            - Original message for all other cases
            - Empty string if blocked
        """
        # Apply stable response if conditions met
        if cls.should_apply_stable_response(command, message):
            return cls.generate_stable_response()
        
        # Strip blocked tokens and return original
        cleaned = cls.strip_blocked_tokens(message)
        
        # If message becomes empty after stripping, return empty
        if not cleaned.strip():
            return ""
        
        return cleaned
    
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
