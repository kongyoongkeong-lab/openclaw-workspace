#!/usr/bin/env python3
"""
Context Budget Estimator for deterministic token counting.
No autonomous governance. No self-repair.
No live RAG auto-write.
"""

import re
from typing import Tuple, Optional

# Token estimation constants
WORD_TOKEN = 0.75  # Average tokens per word (English)
CHAR_TOKEN = 0.08  # Average tokens per character (non-English)
NEWLINE_TOKEN = 0.025
PUNCT_TOKEN = 0.1

# Policy thresholds (LOCKED - Phase H1 Strict Mode)
# Interpretation:
#   0–6850          = normal operation
#   6851–6963       = warning / soft pruning
#   6964–8192       = blocked before model call
#   8193–9536       = emergency burst only, not normal execution
#   >9536           = reject immediately
WARNING_AT = 6850      # 70% of max_context (warning trigger)
BLOCK_AT = 6963        # 85% of max_context (block trigger)
MAX_CONTEXT = 8192     # Hard usable limit (not burst ceiling)
BURST_CEILING = 9536   # Emergency burst ceiling (95%)
OUTPUT_RESERVE = 2000  # 25% reserved for model responses
MAX_LOCAL_CONTEXT = 32768  # Local model context window size
OUTPUT_RESERVE_TOKENS = 2000


def count_tokens_simple(text: str) -> int:
    """Simple token counter for deterministic estimation."""
    if not text:
        return 0
    
    # Remove URL tokens
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'@\S+', '', text)
    
    # Estimate tokens
    word_tokens = len(text.split()) * WORD_TOKEN
    char_tokens = len(text) * CHAR_TOKEN
    newline_tokens = text.count('\n') * NEWLINE_TOKEN
    punct_tokens = sum(c in ',.!?;:"()\x22\x27' for c in text) * PUNCT_TOKEN
    
    return int(word_tokens + char_tokens + newline_tokens + punct_tokens)


def estimate_tokens(prompt: str, system: str = None, messages: Optional[list] = None) -> int:
    """Estimate total tokens for context budget check."""
    # Estimate prompt tokens
    prompt_tokens = count_tokens_simple(prompt)
    
    # Estimate system tokens if provided
    system_tokens = count_tokens_simple(system) if system else 0
    
    # Estimate message tokens if provided
    message_tokens = 0
    if messages:
        for msg in messages:
            if isinstance(msg, dict) and 'content' in msg:
                message_tokens += count_tokens_simple(msg['content'])
            elif isinstance(msg, str):
                message_tokens += count_tokens_simple(msg)
    
    return prompt_tokens + system_tokens + message_tokens


def check_context_budget(
    prompt: str,
    system: str = None,
    messages: Optional[list] = None,
    context_limit: int = 8192,
    heavy_mode: bool = False
) -> Tuple[bool, str, int]:
    """
    Check if context budget allows prompt execution.
    
    Returns:
        (allowed: bool, message: str, tokens_used: int)
    
    Policy:
        - If tokens_used > context_limit * 0.85 → HARD BLOCK
        - If tokens_used > context_limit * 0.70 → WARNING
        - Else → ALLOW
    """
    tokens_used = estimate_tokens(prompt, system, messages)
    
    # Hard block threshold (locked Context Manager v1 policy)
    block_at = BLOCK_AT if context_limit == MAX_CONTEXT else int(context_limit * 0.85)
    warning_at = WARNING_AT if context_limit == MAX_CONTEXT else int(context_limit * 0.70)

    if tokens_used > block_at:
        return False, "Context budget exceeded. Prompt rejected for safety.", tokens_used
    
    # Warning threshold (locked Context Manager v1 policy)
    if tokens_used > warning_at:
        return True, f"Context usage at {tokens_used/context_limit*100:.1f}%. Consider loading summary.", tokens_used
    
    # Normal operation
    return True, "Context budget OK.", tokens_used


def reserve_output_buffer(context_limit: int) -> int:
    """
    Reserve tokens for output generation.
    
    Returns:
        int: Reserved token count (fixed at 2000 for 8192 limit)
    """
    # Reserve 25% of context limit for output
    return OUTPUT_RESERVE_TOKENS


def get_context_policy() -> dict:
    """Return current context policy constants.

    Canonical Context Manager v1 keys are exposed first. Legacy aliases are
    retained for existing callers.
    """
    return {
        "max_context_tokens": MAX_CONTEXT,
        "warning_threshold_tokens": WARNING_AT,
        "block_threshold_tokens": BLOCK_AT,
        "hard_limit_tokens": MAX_CONTEXT,
        "burst_ceiling_tokens": BURST_CEILING,
        "output_reserve_tokens": OUTPUT_RESERVE_TOKENS,
        # Legacy aliases
        "context_limit": MAX_CONTEXT,
        "warning_at": WARNING_AT,
        "block_at": BLOCK_AT,
        "max_local_context": MAX_LOCAL_CONTEXT,
        "output_reserve": OUTPUT_RESERVE_TOKENS,
    }


def load_memory_summary() -> str:
    """Load state_summary.md for context compression."""
    summary_path = "/home/jason2ykk/.openclaw/workspace/memory/state_summary.md"
    try:
        with open(summary_path, "r") as f:
            return f.read()
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    # Test
    prompt = "Hello world" * 1000
    allowed, msg, tokens = check_context_budget(prompt)
    print(f"Allowed: {allowed}, Tokens: {tokens}, Message: {msg}")
