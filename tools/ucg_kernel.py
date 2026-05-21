"""
UCG KERNEL — Stateless Decision Core (G1 Phase 4 Compliant)
==========================================================

INVARANTS (Non-Negotiable):
1. STATELESS — No memory of past decisions
2. NO MEMORY LOOPS — No historical scoring
3. NO ADAPTIVE TUNING — Fixed thresholds only
4. FIXED DECISION SPACE — {NORMAL, THROTTLE, DEFER, ESCALATE}
5. PURE FUNCTION — f(signal_vector) → decision
6. NO IMPORTS FROM EXTERNAL MODULES

This is the MINIMAL cognitive kernel.
No learning. No memory. No recursion.
"""

import json
import os
from typing import Dict, Any, Optional, List


# ------------------------------------------------------------------
# FIXED DECISION SPACE
# ------------------------------------------------------------------

DECISION_ACTIONS = [
    "NORMAL",      # Continue at current level
    "THROTTLE",    # Reduce load/priority
    "DEFER",       # Delay execution
    "ESCALATE"     # Offload to higher authority
]

# CRITICAL SAFETY CONSTRAINT:
# This module MUST NOT import from external modules (no telemetry, no scheduler, no ucg legacy)


# ------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------

DECISION_LOG = "/home/jason2ykk/.openclaw/workspace/memory/decisions.jsonl"


def _ensure_storage() -> None:
    """Ensure decision log directory exists."""
    os.makedirs(os.path.dirname(DECISION_LOG), exist_ok=True)


def _get_current_timestamp() -> str:
    """Return ISO timestamp."""
    from datetime import datetime
    return datetime.utcnow().isoformat() + "Z"


def _generate_decision_id() -> str:
    """Generate unique decision ID."""
    import uuid
    return f"dec_{uuid.uuid4().hex[:8]}"


# ------------------------------------------------------------------
# PUBLIC API (Stateless Decision Interface)
# ------------------------------------------------------------------

def evaluate(signal_vector: Dict[str, Any]) -> Dict[str, Any]:
    """
    Stateless decision evaluation.
    
    PARAMS:
        signal_vector: Current signal state (no history/memory)
    
    RETURNS:
        Decision dict with fixed action space
    
    INVARIANT: Pure function f(signal) → decision. No memory, no learning.
    """
    _ensure_storage()
    
    # Determine action based on signal (deterministic mapping only)
    # No historical scoring, no adaptive thresholds
    
    action = "NORMAL"  # Default
    
    # Simple deterministic thresholds (no learning)
    if signal_vector.get("load") > 0.9:
        action = "THROTTLE"
    elif signal_vector.get("load") > 0.95:
        action = "ESCALATE"
    elif signal_vector.get("load") < 0.2:
        action = "DEFER"
    
    decision = {
        "decision_id": _generate_decision_id(),
        "timestamp": _get_current_timestamp(),
        "action": action,
        "reasoning": f"Signal load {signal_vector.get('load')} → {action}",
        "memory_used": False,  # STATELESS
        "learning_active": False  # NO ADAPTIVE TUNING
    }
    
    # Log decision (stateless log, no memory retention)
    _log_decision(decision)
    
    return decision


def _log_decision(decision: Dict[str, Any]) -> None:
    """
    Log decision (stateless append only).
    
    PARAMS:
        decision: Decision dict from evaluate()
    
    INVARIANT: Stateless log, no memory retention, no learning.
    """
    with open(DECISION_LOG, "a") as f:
        f.write(json.dumps(decision) + "\n")


def get_available_actions() -> List[str]:
    """
    Return fixed decision space.
    
    RETURNS:
        List of action strings
    
    INVARIANT: Fixed action set, no learning.
    """
    return DECISION_ACTIONS


# ------------------------------------------------------------------
# PUBLIC API EXPOSITION
# ------------------------------------------------------------------

__all__ = [
    "evaluate",
    "get_available_actions",
]
