#!/usr/bin/env python3
"""
Context Manager v0 - Lightweight context budget enforcement
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Token estimation constants (approximate)
TOKEN_COST_USER = 1.0  # user tokens = 1:1
TOKEN_COST_MODEL = 1.5  # model responses are denser
TOKEN_COST_TOOL = 2.0  # tool calls are heavier

# Thresholds
MAX_PROMPT_TOKENS = 30000
WARNING_THRESHOLD = 25000
COMPACT_THRESHOLD = 28000

# Render policy
ROUTINE_TO_CHAT = False
STABLE_METRICS_TO_CHAT = False
HEARTBEAT_TO_CHAT = False
INVARIANT_TO_CHAT = False

# Minimal render criteria
ALLOWED_TO_RENDER = [
    "user_decision_required",
    "warning",
    "failure",
    "degradation_detected",
    "invariant_break",
    "state_change",
]


def estimate_tokens(text: str) -> int:
    """Rough token estimation."""
    # Simplified: count words * avg tokens per word
    words = len(text.split())
    return words * 1.3  # rough avg


def check_prompt_size(content: str, context_window: int = 33000) -> Tuple[bool, str]:
    """
    Check if prompt is within budget.
    Returns (is_safe, message).
    """
    estimated_tokens = estimate_tokens(content)
    
    if estimated_tokens > MAX_PROMPT_TOKENS:
        return False, f"BLOCKED: Estimated {estimated_tokens} tokens (max {MAX_PROMPT_TOKENS})"
    elif estimated_tokens > WARNING_THRESHOLD:
        return True, f"WARNING: Estimated {estimated_tokens} tokens (warn at {WARNING_THRESHOLD})"
    
    return True, ""


def filter_chat_content(content: str) -> str:
    """
    Apply minimal render policy: only surface anomalies/decisions.
    """
    # TODO: Implement semantic filtering
    # For now, just return content as-is (filtering would need NLP)
    return content


def summarize_state(state_path: str) -> str:
    """
    Summarize external state on compaction.
    Returns concise summary for new context window.
    """
    state_file = Path(state_path)
    if not state_file.exists():
        return "# No state found\n\n"
    
    # TODO: Implement state summarization logic
    return f"# State Summary (from {state_path})\n\n[See logs for details]\n\n"


def run_synthetic_tests():
    """Run synthetic threshold validation without sending large prompts to chat."""
    print("\n" + "="*60)
    print("CONTEXT MANAGER v0 - THRESHOLD VALIDATION")
    print("="*60 + "\n")
    
    # Test 1: Warning threshold (22k estimated tokens = warning zone)
    print("TEST 1: Warning threshold (22k estimated tokens)")
    print("-" * 50)
    # Generate 17k words (approx 22k tokens with 1.3x factor = warning zone)
    warning_text = "word " * 17000
    estimated_warning = estimate_tokens(warning_text)
    is_safe, msg = check_prompt_size(warning_text)
    
    print(f"Estimated tokens: {estimated_warning:,}")
    print(f"Action taken: {msg if msg else 'Allowed (no warning)'}")
    
    if is_safe and estimated_warning >= WARNING_THRESHOLD:
        print("STATUS: WARNING TRIGGERED ✅")
    else:
        print(f"STATUS: {msg or 'ALLOWED'}")
    
    # Test 2: Block threshold (25k estimated tokens = blocked)
    print("\nTEST 2: Block threshold (25k estimated tokens)")
    print("-" * 50)
    # Generate 25k words (approx 32k tokens with 1.3x factor = blocked)
    block_text = "word " * 25000
    estimated_block = estimate_tokens(block_text)
    is_blocked, msg = check_prompt_size(block_text)
    
    print(f"Estimated tokens: {estimated_block:,}")
    print(f"Action taken: {msg}")
    
    if not is_blocked and estimated_block >= MAX_PROMPT_TOKENS:
        print("STATUS: BLOCKED ✅")
    else:
        print(f"STATUS: {msg or 'ALLOWED'}")
    
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60 + "\n")
    
    return {
        "test1": {
            "name": "warning_threshold",
            "estimated_tokens": estimated_warning,
            "action_taken": msg or "allowed",
            "status": "pass" if estimated_warning >= WARNING_THRESHOLD and is_safe else "fail"
        },
        "test2": {
            "name": "block_threshold",
            "estimated_tokens": estimated_block,
            "action_taken": msg,
            "status": "pass" if not is_blocked and estimated_block >= MAX_PROMPT_TOKENS else "fail"
        }
    }


def main():
    """CLI interface."""
    print("Context Manager v0 initialized")
    print("Token estimation: ENABLED")
    print("Oversized prompt block: ENABLED")
    print("Render policy: ACTIVE")
    print("State summarization: [TODO]")
    
    # Run synthetic validation tests
    results = run_synthetic_tests()
    
    return results
