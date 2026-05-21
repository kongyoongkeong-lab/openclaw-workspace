#!/usr/bin/env python3
"""
Context Builder - v1
Final safety layer: constructs safe prompt from user input + gated memory
"""

from memory_gate import memory_gate


def build_context(user_input, retrieved_memory):
    """
    SAFE CONTEXT BUILDER
    
    1. Retrieves memory (already filtered to top-k)
    2. Applies gate (token budget enforcement)
    3. Constructs final safe prompt
    """
    # CRITICAL: Apply gate BEFORE building context
    gated = memory_gate(retrieved_memory, max_tokens=8000)

    memory_block = "\n".join([
        f"[{m.get('timestamp', '')}] {m.get('text', '')}"
        for m in gated
    ])

    return f"""USER:
{user_input}

MEMORY:
{memory_block}
"""


if __name__ == "__main__":
    # Test builder
    test_memory = [
        {"text": "Project setup complete", "timestamp": "2026-05-06"},
        {"text": "VRAM at 85%, compression active", "timestamp": "2026-05-06"},
    ]
    user_input = "Deploy production build"
    context = build_context(user_input, test_memory)
    print(context)
    print(f"\nTotal chars: {len(context)}")
