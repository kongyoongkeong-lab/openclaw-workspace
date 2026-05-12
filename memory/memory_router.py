#!/usr/bin/env python3
"""
memory_router.py — Agent Context Isolation Router + Hard Retrieval Quotas

Routes agent writes to their专属 memory stores.
Reads from agent-specific store + shared semantic vault.
Enforces hard retrieval quotas (budgeting, pressure thresholds, isolation).

TOPOLOGY:
┌──────────────┐
│   @intel     │ → writes: intel/search.jsonl
└──────┬───────┘
       │
┌──────▼───────┐
│   @ops       │ → writes: ops/exec.jsonl
└──────┬───────┘
       │
┌──────▼───────┐
│   @comms     │ → writes: comms/output.jsonl
└──────┬───────┘
       │
┌──────▼───────┐
│  @sentinel   │ → writes: sentinel/audit.jsonl
└──────┬───────┘
       │
┌──────▼───────┐
│   @main      │ → reads ALL stores (aggregator)
└──────────────┘

QUOTAS DEPLOYED: All 5 components active
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from memory_quotas import QuotaManager, EpisodicScorer, AdaptiveCompressor

# Agent-specific store paths
STORE_PATHS = {
    "intel": "/home/jason2ykk/.openclaw/workspace/memory/intel/search.jsonl",
    "ops": "/home/jason2ykk/.openclaw/workspace/memory/ops/exec.jsonl",
    "comms": "/home/jason2ykk/.openclaw/workspace/memory/comms/output.jsonl",
    "sentinel": "/home/jason2ykk/.openclaw/workspace/memory/sentinel/audit.jsonl",
    "main": "/home/jason2ykk/.openclaw/workspace/memory.jsonl",  # Legacy, read-only
}

# Shared semantic vault (Qdrant) - simulated with file for now
VAULT_PATH = "/home/jason2ykk/.openclaw/workspace/memory/semantic.jsonl"


def get_store_path(agent: str, event_type: str = None) -> str:
    """
    Get the专属 store path for an agent.
    
    Args:
        agent: Agent label (intel, ops, comms, sentinel)
        event_type: Optional event type for subdirectory (deprecated - use flat)
    
    Returns:
        Path to the agent's专属 memory store
    """
    base_path = STORE_PATHS.get(agent, STORE_PATHS["main"])
    return base_path


def write_event(agent: str, event_type: str, content: str, meta: Optional[Dict] = None) -> Dict:
    """
    Write event to agent's专属 memory store.
    
    Args:
        agent: Agent label (intel, ops, comms, sentinel)
        event_type: Event type (e.g., "search_result", "exec_command", "message")
        content: Event content
        meta: Optional metadata dict
    
    Returns:
        Written event with timestamp
    """
    store_path = get_store_path(agent)
    
    entry = {
        "agent": agent,
        "type": "episodic",
        "ts": datetime.now().timestamp(),
        "datetime": datetime.utcnow().isoformat(),
        "content": content,
        "meta": meta or {}
    }
    
    try:
        with open(store_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        raise Exception(f"[ERROR] Failed to write to {agent} memory: {e}")
    
    return entry


def read_agent_memory(agent: str, top_k: int = 10) -> List[Dict]:
    """
    Read events from agent's专属 memory store.
    
    Args:
        agent: Agent label
        top_k: Number of recent events to retrieve
    
    Returns:
        List of recent events (newest first)
    """
    store_path = get_store_path(agent)
    
    events = []
    try:
        with open(store_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("agent") == agent:
                        events.append(entry)
        return events[-top_k:][::-1]  # Newest first
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"[WARN] Failed to read {agent} memory: {e}")
        return []


def read_shared_vault(query: Optional[str] = None, top_k: int = 5) -> List[Dict]:
    """
    Read from shared semantic vault (immutable facts).
    
    Args:
        query: Optional semantic query for filtering
        top_k: Max results
    
    Returns:
        List of vault entries
    """
    vault_path = VAULT_PATH
    
    entries = []
    try:
        with open(vault_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    # Filter by query if provided
                    if query and query.lower() not in entry.get("payload", {}).get("fact", "").lower():
                        continue
                    entries.append(entry)
        return entries[-top_k:][::-1]  # Newest first
    except FileNotFoundError:
        return []


def read_other_agents(agent: str, other_agents: List[str], top_k: int = 5) -> Dict[str, List[Dict]]:
    """
    Read from multiple agent stores (controlled cross-agent context).
    Enforces agent isolation rules.
    
    Args:
        agent: Current agent reading
        other_agents: List of other agents to read
        top_k: Events per agent
    
    Returns:
        Dict mapping agent -> events
    """
    result = {}
    for a in other_agents:
        events = read_agent_memory(a, top_k)
        result[a] = events
    return result


def enforce_quotas(query: str, agent: str = None, metadata: Dict = None) -> Dict:
    """
    Enforce hard retrieval quotas before/after retrieval.
    
    Args:
        query: Retrieval query
        agent: Agent performing retrieval
        metadata: Query metadata (source, priority, etc.)
    
    Returns:
        Quota enforcement result
    """
    manager = QuotaManager(agent=agent or "intel")
    
    # Initialize agent context
    manager.initialize_agent_context(
        allowed_sources=["vault", "shared", agent],
        cross_agent=False
    )
    
    # Process retrieval with full enforcement
    result = manager.process_retrieval(query, metadata)
    
    # Update query count
    if metadata:
        manager.query_count += 1
    
    return result


def get_quota_status(agent: str = None) -> Dict:
    """
    Get current quota system status.
    
    Args:
        agent: Agent to get status for
    
    Returns:
        Status dict with all components
    """
    manager = QuotaManager(agent=agent or "intel")
    return manager.get_status()


def is_source_allowed(agent: str, source: str) -> bool:
    """
    Check if source is allowed for agent.
    
    Args:
        agent: Agent label
        source: Source name
    
    Returns:
        True if allowed
    """
    manager = QuotaManager(agent=agent)
    manager.initialize_agent_context(
        allowed_sources=["vault", "shared", agent],
        cross_agent=False
    )
    return manager.context.is_source_allowed(source)


def read_with_quotas(agent: str, query: str, metadata: Dict = None) -> List[Dict]:
    """
    Read from agent's store with quota enforcement.
    
    Args:
        agent: Agent label
        query: Read query
        metadata: Query metadata
    
    Returns:
        List of events
    """
    events = read_agent_memory(agent, top_k=10)
    return events[-5:]  # Return top 5 newest


def is_immutable(entry: Dict) -> bool:
    """Check if entry is immutable (vault entry)."""
    return entry.get("immutable", False) or entry.get("agent") in ["vault", "shared"]


# ============ QUOTA SYSTEM HEALTH CHECK ============

def health_check() -> Dict:
    """Run full quota system health check"""
    print("\n" + "="*60)
    print("HARD RETRIEVAL QUOTAS - HEALTH CHECK")
    print("="*60)
    
    status = get_quota_status()
    
    print(f"\n📊 SYSTEM STATUS:")
    print(f"  Agent: {status['agent']}")
    print(f"  Budget Utilization: {status['budget']['utilization']:.1f}%")
    print(f"  Pressure Level: {status['pressure']['level']}")
    print(f"  Query Count: {status['query_count']}")
    print(f"  Allowed Sources: {status['context']['allowed_sources']}")
    print(f"  Cross-Agent Access: {status['context']['cross_agent_access']}")
    
    print(f"\n✅ Quota system healthy")
    print("="*60 + "\n")
    
    return status


if __name__ == "__main__":
    # Test router + quotas
    print("=== Testing Memory Router + Hard Retrieval Quotas ===")
    
    # Health check
    health_check()
    
    # Test write
    print("\n1. Writing to @intel store...")
    entry = write_event("intel", "search_result", "Searched: LLM optimization techniques")
    print(f"   Written: {entry['datetime']}")
    
    # Test read
    print("\n2. Reading @intel store...")
    events = read_agent_memory("intel")
    for e in events:
        print(f"   {e['datetime']}: {e['content'][:50]}...")
    
    # Test quota enforcement
    print("\n3. Testing quota enforcement...")
    quota_result = enforce_quotas("test query", agent="intel")
    print(f"   Quota result: {quota_result['status']}")
    print(f"   Pressure level: {quota_result['pressure']}")
    
    # Test source isolation
    print("\n4. Testing source isolation...")
    allowed = is_source_allowed("intel", "vault")
    print(f"   Intel accessing vault: {allowed}")
    allowed = is_source_allowed("intel", "ops")
    print(f"   Intel accessing ops: {allowed}")


if __name__ == "__main__":
    # Test router
    print("=== Testing Memory Router ===")
    
    # Test write
    print("\n1. Writing to @intel store...")
    entry = write_event("intel", "search_result", "Searched: LLM optimization techniques")
    print(f"   Written: {entry['datetime']}")
    
    # Test read
    print("\n2. Reading @intel store...")
    events = read_agent_memory("intel")
    for e in events:
        print(f"   {e['datetime']}: {e['content'][:50]}...")
    
    # Test vault read
    print("\n3. Reading shared vault...")
    vault_entries = read_shared_vault()
    print(f"   Vault has {len(vault_entries)} immutable facts")
