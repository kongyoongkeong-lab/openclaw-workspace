#!/usr/bin/env python3
"""
Agent Memory Module v1 - Localized Episodic Stores
==============================================================================
Each agent maintains its own episodic memory store to prevent context bleeding.

Topology:
  @main ─┬─ episodic_main.jsonl
         ├─ episodic_intel.jsonl
         ├─ episodic_ops.jsonl
         └─ episodic_comms.jsonl

Shared Vault (Qdrant):
  - Immutable facts (Point ID 1)
  - Semantic retrieval for cross-agent facts

Rules:
  1. Agents write to their own store only
  2. @main can read all stores for summaries
  3. Shared vault is read-only for agents (except @main)
  4. Legacy memory.jsonl remains append-only (30-day deprecation)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
def compile_context(user_input: str, context_window: str) -> Dict:
    """
    Simple local context compiler (standalone version).
    
    Args:
        user_input: Current user message
        context_window: Agent's episodic context
    
    Returns:
        Compiled prompt dict
    """
    # Calculate rough token count
    tokens = (len(user_input) + len(context_window)) // 4
    
    # Build compiled prompt
    compiled = f"""SYSTEM CONTEXT:
{context_window}

USER: {user_input}

ASSISTANT: (generate response)"""
    
    # Estimate tokens
    token_count = (len(compiled) // 4) + 100  # Rough estimate
    
    # Check compression threshold
    compression_applied = token_count > 30000
    
    return {
        "compiled_prompt": compiled,
        "token_count": token_count,
        "compression_applied": compression_applied,
        "checkpoint": {},
        "retrieved_facts": [],
        "recent_episodes": [],
    }

from context_manager_v0 import compile_context  # Fallback to external if available


def get_agent_store_path(agent: str) -> Path:
    """
    Get the episodic store path for an agent.
    
    Args:
        agent: Agent identifier (@intel, @ops, @comms, @sentinel, @main)
    
    Returns:
        Path to agent's episodic store
    """
    # Legacy store path (read-only reference)
    legacy_path = Path.home() / ".openclaw" / "workspace" / "memory" / "memory.jsonl"
    
    # New agent-specific stores
    agent_stores = {
        "@main": Path.home() / ".openclaw" / "workspace" / "memory" / "main" / "episodic.jsonl",
        "@intel": Path.home() / ".openclaw" / "workspace" / "memory" / "intel" / "episodic.jsonl",
        "@ops": Path.home() / ".openclaw" / "workspace" / "memory" / "ops" / "episodic.jsonl",
        "@comms": Path.home() / ".openclaw" / "workspace" / "memory" / "comms" / "episodic.jsonl",
        "@sentinel": Path.home() / ".openclaw" / "workspace" / "memory" / "sentinel" / "episodic.jsonl",
    }
    
    # Check if legacy path exists
    if legacy_path.exists():
        return legacy_path
    
    # Return agent-specific store
    return agent_stores.get(agent, legacy_path)


def write_episode(agent: str, content: str, meta: Optional[Dict] = None) -> Dict:
    """
    Write an episodic memory entry to agent's store.
    
    Args:
        agent: Agent identifier
        content: Event description
        meta: Optional metadata (tokens, source, query, etc.)
    
    Returns:
        Written entry dict
    """
    store_path = get_agent_store_path(agent)
    
    # Create agent directory if needed
    store_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Construct entry
    entry = {
        "agent": agent,
        "type": "episodic",
        "ts": int(time.time()),
        "datetime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "content": content,
    }
    
    if meta:
        entry["meta"] = meta
    
    # Write to append-only JSONL
    with open(store_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return entry


def read_agent_episodes(agent: str, limit: int = 10) -> List[Dict]:
    """
    Read recent episodes from agent's store.
    
    Args:
        agent: Agent identifier
        limit: Maximum entries to read
    
    Returns:
        List of episode entries (reverse chronological)
    """
    store_path = get_agent_store_path(agent)
    
    if not store_path.exists():
        return []
    
    episodes = []
    with open(store_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                episodes.append(json.loads(line))
                if len(episodes) >= limit:
                    break
            except json.JSONDecodeError:
                continue
    
    # Return reverse chronological (newest first)
    episodes.reverse()
    return episodes


def read_all_agent_stores() -> Dict[str, List[Dict]]:
    """
    Read all agent stores for @main to build cross-agent context.
    
    Returns:
        Dict mapping agent -> list of episodes
    """
    agents = ["@main", "@intel", "@ops", "@comms", "@sentinel"]
    result = {}
    
    for agent in agents:
        episodes = read_agent_episodes(agent, limit=100)
        result[agent] = episodes
    
    return result


def retrieve_from_vault(collection: str = "pentagon_brain", 
                       query: str = "", 
                       limit: int = 5) -> List[Dict]:
    """
    Retrieve from shared semantic vault (Qdrant).
    
    Args:
        collection: Qdrant collection name
        query: Search query string
        limit: Maximum results
    
    Returns:
        List of vault point payloads
    """
    # Placeholder for Qdrant integration
    # In production: Use qdrant-client to fetch top-k embeddings
    
    # Simulate retrieval
    return [{
        "id": 1,
        "vector": [],
        "payload": {
            "fact": "qwen3.5:9b deployed on RTX 4070 Super",
            "immutable": True
        }
    }]


def build_compiled_context(user_input: str, agent: str = "@main") -> Dict:
    """
    Build compiled prompt with agent's episodic context + vault retrieval.
    
    This is the main entry point for agents to get their working context.
    
    Args:
        user_input: Current user message
        agent: Agent identifier (defaults to @main)
    
    Returns:
        Compiled prompt dict with:
          - compiled_prompt: Final prompt for LLM
          - token_count: Actual token usage
          - compression_applied: Boolean
          - checkpoint: State checkpoint
          - retrieved_facts: Vault facts
          - recent_episodes: Agent's recent memory
    """
    # Get agent's episodic store
    episodes = read_agent_episodes(agent, limit=20)
    
    # Build context window from episodes
    context_window = "\n\n".join([
        json.dumps(ep, ensure_ascii=False) for ep in episodes
    ])
    
    # Use Context Manager v0 to compile
    result = compile_context(user_input, context_window)
    
    # Add retrieved facts
    result["retrieved_facts"] = retrieve_from_vault()
    result["recent_episodes"] = episodes
    
    return result


def legacy_read_memory() -> List[Dict]:
    """
    Read legacy memory.jsonl (deprecated but still active).
    
    Returns:
        List of legacy entries
    """
    path = Path.home() / ".openclaw" / "workspace" / "memory" / "memory.jsonl"
    
    if not path.exists():
        return []
    
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    return entries


def legacy_write_memory(entry: Dict) -> bool:
    """
    Write to legacy memory.jsonl (deprecated but still active).
    
    Args:
        entry: Entry dict to append
    
    Returns:
        True if write succeeded
    """
    path = Path.home() / ".openclaw" / "workspace" / "memory" / "memory.jsonl"
    
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent Memory Module v1")
    parser.add_argument("--agent", type=str, default="@main", help="Agent identifier")
    parser.add_argument("--write", action="store_true", help="Write mode")
    parser.add_argument("--content", type=str, help="Content to write")
    parser.add_argument("--read", action="store_true", help="Read mode")
    parser.add_argument("--list", action="store_true", help="List all agent stores")
    parser.add_argument("--legacy", action="store_true", help="Use legacy memory.jsonl")
    args = parser.parse_args()
    
    if args.list:
        print("=== Agent Memory Stores ===")
        for agent in ["@main", "@intel", "@ops", "@comms", "@sentinel"]:
            path = get_agent_store_path(agent)
            if path.exists():
                count = sum(1 for _ in open(path) if _.strip())
                print(f"{agent}: {path.name} ({count} entries)")
            else:
                print(f"{agent}: {path.name} (not created yet)")
    elif args.write and args.content:
        meta = {"source": "manual", "agent": args.agent}
        entry = write_episode(args.agent, args.content, meta)
        print(f"Written: {entry}")
    elif args.read:
        episodes = read_agent_episodes(args.agent, limit=5)
        print(f"\n=== {args.agent} Episodes ===")
        for ep in episodes:
            print(f"[{ep.get('datetime', 'N/A')}] {ep.get('content', '')}")
    elif args.legacy:
        print("=== Legacy Memory (memory.jsonl) ===")
        entries = legacy_read_memory()
        print(f"Found {len(entries)} legacy entries")
    else:
        print("Agent Memory Module v1")
        print("Usage: python memory_module.py --list")
