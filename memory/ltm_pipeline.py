#!/usr/bin/env python3
"""
ltm_pipeline.py — Memory LTM Full Pipeline Orchestrator

Pipeline: LOAD → RETRIEVE → GATE → BUILD → LLM
Single source of truth: memory.jsonl
"""

import json
import sys
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_store import write_event, count_lines
from memory_retriever import retrieve
from memory_gate import memory_gate, estimate_tokens
from context_builder import build_context

MAX_TOKENS = 8000

def run_pipeline(user_input: str):
    """
    Run complete LTM pipeline
    
    1. LOAD full memory.jsonl
    2. RETRIEVE top-k relevant entries
    3. GATE token budget (hard firewall)
    4. BUILD context (safe prompt)
    5. Return context for LLM
    """
    
    # Step 1: LOAD full memory store (single source of truth)
    memory_file = "/home/jason2ykk/.openclaw/workspace/memory.jsonl"
    try:
        with open(memory_file, "r", encoding="utf-8") as f:
            all_memory = [json.loads(line) for line in f if line.strip()]
        write_event("pipeline_load", f"Loaded {len(all_memory)} events", {"total_lines": len(all_memory)})
    except Exception as e:
        raise Exception(f"Failed to load memory: {e}")
    
    # Step 2: RETRIEVE relevant subset (top-k)
    try:
        candidates = retrieve(user_input, top_k=50)
        write_event("pipeline_retrieve", f"Retrieved {len(candidates)} candidates", {"k": 50})
    except Exception as e:
        raise Exception(f"Failed to retrieve memory: {e}")
    
    # Step 3: GATE token budget (HARD FIREWALL)
    try:
        safe_memory = memory_gate(candidates, max_tokens=MAX_TOKENS)
        total_tokens = sum(estimate_tokens(e["content"]) for e in safe_memory)
        write_event("pipeline_gate", f" gated {len(safe_memory)}/{len(candidates)} entries, {total_tokens}/{MAX_TOKENS} tokens", {"safe_count": len(safe_memory), "total_tokens": total_tokens})
    except Exception as e:
        raise Exception(f"Failed to gate memory: {e}")
    
    # Step 4: BUILD context (safe prompt assembly)
    try:
        context = build_context(user_input, safe_memory)
        write_event("pipeline_build", f"Built context ({len(safe_memory)} memory entries + user input)", {"context_length": len(context)})
    except Exception as e:
        raise Exception(f"Failed to build context: {e}")
    
    # Return context for LLM
    return context

if __name__ == "__main__":
    # Test pipeline
    test_input = "Deploy production build with memory compression"
    print("=== Testing LTM Pipeline ===")
    print(f"User input: {test_input}")
    print("-" * 50)
    
    context = run_pipeline(test_input)
    
    print("\n=== Context Built Successfully ===")
    print(f"Context length: {len(context)} chars")
    print("\nContext Preview:")
    print(context[:500] + "..." if len(context) > 500 else context)
