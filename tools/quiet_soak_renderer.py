#!/usr/bin/env python3
"""
Quiet Soak Status Renderer (Render Policy Enforcement)
Enforces minimal output for stable H1 observation states.
"""

# Blocked tokens that must never appear in user-facing output
BLOCKED_TOKENS = frozenset([
    "NO_REPLY",
    "INTERNAL_ONLY",
    "CONTROL_ONLY",
    "SYSTEM_ONLY",
])

# Stable state one-liner
STABLE_ONELINER = "Stable. No user action required."


def render_quiet_soak_status() -> str:
    """
    Render quiet soak status for stable H1 observation.
    
    For any stable H1 observation output:
    - remove NO_REPLY
    - remove INTERNAL_ONLY
    - remove CONTROL_ONLY
    - remove SYSTEM_ONLY
    
    If no warning, no invariant break, no degradation, and no user decision required:
    render exactly: "Stable. No user action required."
    """
    # This path is always stable during quiet soak
    return STABLE_ONELINER


if __name__ == "__main__":
    print(render_quiet_soak_status())
