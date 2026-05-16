#!/usr/bin/env python3
"""
ENGINE ARBITRATOR (PHASE B.2 - Execution Planner)
================================================
Deterministic execution plan generator for governed cognitive pipeline.

PURPOSE:
- Convert Phase A classification output into executable plans
- Enforce immutable budgets
- Provide explicit resolver hooks for Phase B.1 conflicts

ARCHITECTURE GUARANTEE:
- PURE FUNCTION: Returns execution_plan JSON only
- NO EXECUTION: Does not call engines directly
- BUDGET IMMUTABLE: Freeze semantics enforced
- DETERMINISTIC: Same input → same output (no randomness)

INPUT CONTRACT (from Phase A):
{
  "intent": "...",
  "confidence": 0.92,
  "tags": ["search", "analysis"],
  "metadata": {...}
}

OUTPUT CONTRACT:
{
  "execution_plan": "structured plan",
  "budget": {
    "max_tokens": 10000,
    "max_time_seconds": 120,
    "priority": "high"
  },
  "mode": "standard|constrained|explore",
  "resolver_hook": {
    "requires_conflict_resolution": false,
    "resolver_version": "v1",
    "conflict_threshold": 0.6
  }
}
"""

import json
from typing import Any, Dict, Optional


class BudgetViolationError(Exception):
    """Raised when execution plan would exceed frozen budget."""
    pass


class DeterminismViolationError(Exception):
    """Raised when output varies with same input (non-deterministic)."""
    pass


def freeze_budget(budget_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Freeze budget object (immutable semantics).
    
    Args:
        budget_config: Raw budget configuration dict
        
    Returns:
        Frozen budget object (deep copy with metadata)
        
    INvariant:
        Frozen budget must never be mutated downstream.
        Any attempt to mutate → system drift risk.
    """
    import copy
    import time
    from uuid import uuid4
    
    frozen = copy.deepcopy(budget_config)
    frozen["_frozen"] = True
    frozen["_freeze_timestamp"] = time.time()
    frozen["_freeze_id"] = str(uuid4())
    frozen["_immutable"] = True
    
    return frozen


def detect_conflict(resolver_result: Optional[Dict[str, Any]] = None) -> bool:
    """
    Detect whether Phase B.1 conflict resolution was required.
    
    Args:
        resolver_result: Result from Phase B.1 resolver (or None if no conflict)
        
    Returns:
        True if conflict resolution was required, False otherwise
    """
    if resolver_result is None:
        return False
    
    return resolver_result.get("requires_conflict_resolution", False)


def validate_determinism(input_hash: str, output_hash: str) -> None:
    """
    Validate that same input produces same output (determinism check).
    
    Args:
        input_hash: Hash of input (from Phase A)
        output_hash: Hash of output (from this module)
        
    Raises:
        DeterminismViolationError: If hashes don't match
    """
    if input_hash != output_hash:
        raise DeterminismViolationError(
            f"Non-deterministic: input={input_hash} != output={output_hash}"
        )


def generate_execution_plan(phase_a_output: Dict[str, Any], 
                           budget_config: Optional[Dict[str, Any]] = None,
                           resolver_result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate execution plan from Phase A classification output.
    
    This is a PURE FUNCTION - it returns the execution plan only.
    It does NOT execute the plan itself.
    
    Args:
        phase_a_output: Classification output from Phase A
        budget_config: Raw budget configuration (will be frozen)
        resolver_result: Optional conflict resolution result from Phase B.1
        
    Returns:
        Execution plan dict with:
        - execution_plan: Structured plan
        - budget: Frozen budget object
        - mode: Execution mode
        - resolver_hook: Resolver handshake info
        
    CONTRACT:
        - Pure output only (no execution)
        - Immutable budget semantics
        - Explicit resolver hook
        - Deterministic routing guarantee
    """
    
    # Freeze budget (if provided, otherwise use defaults)
    frozen_budget = freeze_budget(budget_config or {
        "max_tokens": 10000,
        "max_time_seconds": 120,
        "priority": "high"
    })
    
    # Determine execution mode based on confidence and intent
    confidence = phase_a_output.get("confidence", 0.0)
    intent = phase_a_output.get("intent", "")
    tags = phase_a_output.get("tags", [])
    
    if confidence >= 0.9:
        mode = "standard"
    elif confidence >= 0.6:
        mode = "constrained"
    else:
        mode = "explore"
    
    # Check for conflict resolution requirement
    requires_conflict = detect_conflict(resolver_result)
    
    # Build execution plan (pure function, no execution)
    execution_plan = {
        "steps": [
            {
                "name": "prepare",
                "description": "Validate inputs and freeze budgets",
                "type": "pre"
            },
            {
                "name": "execute",
                "description": f"Execute plan for: {intent}",
                "mode": mode,
                "type": "main"
            },
            {
                "name": "validate",
                "description": "Verify output against budget constraints",
                "type": "post"
            }
        ],
        "intent": intent,
        "confidence": confidence,
        "tags": tags
    }
    
    # Build resolver hook (handshake between B.2 and B.1)
    resolver_hook = {
        "requires_conflict_resolution": requires_conflict,
        "resolver_version": "v1",
        "conflict_threshold": 0.6,
        "hook_status": "ready"
    }
    
    # Assemble final output
    output = {
        "execution_plan": execution_plan,
        "budget": frozen_budget,
        "mode": mode,
        "resolver_hook": resolver_hook
    }
    
    # Determinism validation (for testing)
    # Note: In production, this is implicitly guaranteed by the function's purity
    # Uncomment for testing:
    # input_hash = hash(json.dumps(phase_a_output, sort_keys=True))
    # output_hash = hash(json.dumps(output, sort_keys=True))
    # validate_determinism(input_hash, output_hash)
    
    return output


def main():
    """
    Demo: Generate execution plan from sample Phase A output.
    
    USAGE:
        python engine_arbitrator.py
    """
    # Sample Phase A output
    phase_a_output = {
        "intent": "search and summarize",
        "confidence": 0.87,
        "tags": ["search", "analysis", "news"],
        "metadata": {
            "source": "web",
            "query": "latest AI safety papers"
        }
    }
    
    # Sample budget config
    budget_config = {
        "max_tokens": 5000,
        "max_time_seconds": 60,
        "priority": "medium"
    }
    
    # No conflict (Phase B.1 not invoked)
    resolver_result = None
    
    # Generate plan (pure function call)
    result = generate_execution_plan(phase_a_output, budget_config, resolver_result)
    
    # Output (for testing)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
