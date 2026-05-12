#!/usr/bin/env python3
"""
ltm_pipeline_isolated.py — Isolated Memory LTM Full Pipeline

Pipeline: LOAD (agent-specific) → RETRIEVE → GATE → BUILD → LLM
Each agent uses their专属 memory store + shared vault

TOPOLOGY:
┌─────────────────────────────────────────┐
│     Shared Semantic Vault (Qdrant)     │
│  (Immutable facts, all agents read)    │
└─────────────────────────────────────────┘
                  ▲
    ┌─────────────┼─────────────┬─────────────┐
    │   @intel    │    @ops     │   @comms    │
    │  search.jsonl  exec.jsonl  output.jsonl  │
    │ (Read-only)   (Read-only)  (Read-only)  │
    └─────────────┴─────────────┴─────────────┘

Usage:
    python ltm_pipeline_isolated.py --agent intel --query "LLM optimization"
    python ltm_pipeline_isolated.py --agent ops --query "Docker deployment"
"""

import json
import sys
import argparse
from datetime import datetime
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_router import write_event, read_agent_memory, read_shared_vault
from memory_retriever import IsolatedRetriever

# Agent-specific store paths
AGENT_STORES = {
    "intel": "/home/jason2ykk/.openclaw/workspace/memory/intel/search.jsonl",
    "ops": "/home/jason2ykk/.openclaw/workspace/memory/ops/exec.jsonl",
    "comms": "/home/jason2ykk/.openclaw/workspace/memory/comms/output.jsonl",
    "sentinel": "/home/jason2ykk/.openclaw/workspace/memory/sentinel/audit.jsonl",
}

# Shared vault path
VAULT_PATH = "/home/jason2ykk/.openclaw/workspace/memory/semantic.jsonl"

# Token budgets (per agent)
TOKEN_BUDGETS = {
    "intel": 2000,
    "ops": 3000,
    "comms": 1500,
    "sentinel": 1000,
}


def estimate_tokens(text: str) -> int:
    """Estimate token count (rough approximation)"""
    # Approx: 1 token ≈ 4 chars
    return len(text) // 4


def run_pipeline(agent: str, user_input: str) -> str:
    """
    Run isolated LTM pipeline for a specific agent
    
    Args:
        agent: Agent label (intel, ops, comms, sentinel)
        user_input: User query/input
    
    Returns:
        Context string for LLM
    """
    
    # Step 1: LOAD agent-specific memory store
    store_path = AGENT_STORES.get(agent, VAULT_PATH)
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            all_memory = [json.loads(line) for line in f if line.strip()]
        
        # Write load event to agent's store
        write_event(
            agent=agent,
            event_type="pipeline_load",
            content=f"Loaded {len(all_memory)} events from {agent} memory store",
            meta={"total_lines": len(all_memory), "source": store_path}
        )
    except FileNotFoundError:
        print(f"[WARN] Agent {agent} store not found: {store_path}")
        all_memory = []
    except Exception as e:
        raise Exception(f"[ERROR] Failed to load {agent} memory: {e}")
    
    # Step 2: RETRIEVE relevant subset (agent-specific + shared vault)
    try:
        retriever = IsolatedRetriever(agent=agent)
        candidates = retriever.retrieve(
            user_input,
            query_type="search" if agent == "intel" else ("execution" if agent == "ops" else "output"),
            top_k=30  # Agent-specific retrieval budget
        )
        
        write_event(
            agent=agent,
            event_type="pipeline_retrieve",
            content=f"Retrieved {len(candidates)} candidates for {agent}",
            meta={"k": 30, "agent": agent}
        )
    except Exception as e:
        raise Exception(f"[ERROR] Failed to retrieve {agent} memory: {e}")
    
    # Step 3: GATE token budget (HARD FIREWALL - agent-specific)
    max_tokens = TOKEN_BUDGETS.get(agent, 2000)
    try:
        safe_memory = []
        total_tokens = 0
        for entry in candidates:
            tokens = estimate_tokens(entry.get("content", ""))
            if total_tokens + tokens <= max_tokens:
                safe_memory.append(entry)
                total_tokens += tokens
        
        write_event(
            agent=agent,
            event_type="pipeline_gate",
            content=f"Gated {len(safe_memory)}/{len(candidates)} entries for {agent}",
            meta={
                "safe_count": len(safe_memory),
                "total_tokens": total_tokens,
                "budget": max_tokens,
                "agent": agent
            }
        )
    except Exception as e:
        raise Exception(f"[ERROR] Failed to gate {agent} memory: {e}")
    
    # Step 4: BUILD context (agent-specific prompt assembly)
    try:
        # Build context: agent memory + user input
        context_parts = [user_input]
        context_parts.append("--- MEMORY CONTEXT ---")
        
        for entry in safe_memory:
            content = entry.get("content", "")
            # Truncate long content
            if len(content) > 1000:
                content = content[:1000] + "..."
            context_parts.append(content)
        
        context = "\n".join(context_parts)
        
        write_event(
            agent=agent,
            event_type="pipeline_build",
            content=f"Built context ({len(safe_memory)} memory entries + user input)",
            meta={"context_length": len(context), "agent": agent}
        )
    except Exception as e:
        raise Exception(f"[ERROR] Failed to build {agent} context: {e}")
    
    # Return context for LLM
    return context


if __name__ == "__main__":
    # Test pipeline with different agents
    parser = argparse.ArgumentParser(description="Isolated LTM Pipeline")
    parser.add_argument("--agent", type=str, default="intel", help="Agent (intel/ops/comms/sentinel)")
    parser.add_argument("--query", type=str, default="LLM optimization", help="User query")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print(f"=== Testing {args.agent.title()} LTM Pipeline ===")
    print(f"User input: {args.query}")
    print("-" * 50)
    
    try:
        context = run_pipeline(agent=args.agent, user_input=args.query)
        
        print(f"\n=== Context Built Successfully for @{args.agent} ===")
        print(f"Context length: {len(context)} chars")
        
        if args.verbose and len(context) > 200:
            print("\nContext Preview:")
            print(context[:200] + "..." if len(context) > 200 else context)
        else:
            print(context)
        
        print(f"\n✅ Pipeline completed for @{args.agent}")
        print(f"   - Loaded: agent-specific memory store")
        print(f"   - Retrieved: top-k relevant entries")
        print(f"   - Gated: token budget enforced")
        print(f"   - Built: safe prompt context")
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)
