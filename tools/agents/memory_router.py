#!/usr/bin/env python3
"""
Memory Router v1 - Route Writes to Agent-Specific Stores
==============================================================================

Routes:
  - Each agent writes to their own episodic store
  - Shared vault (Qdrant) for immutable facts
  - Legacy memory.jsonl remains append-only (deprecated)

Topology:
  @main → episodic_main.jsonl
  @intel → episodic_intel.jsonl
  @ops → episodic_ops.jsonl
  @comms → episodic_comms.jsonl
  @sentinel → episodic_sentinel.jsonl

Shared Vault:
  Qdrant collection: pentagon_brain
  Point ID 1: Immutable facts (hardware baseline, preferences, etc.)
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from memory_module import (
    get_agent_store_path, 
    write_episode, 
    read_agent_episodes,
    retrieve_from_vault
)


class MemoryRouter:
    """
    Routes agent operations to their localized memory stores.
    """
    
    def __init__(self, legacy_compat: bool = True):
        """
        Initialize router.
        
        Args:
            legacy_compat: Enable backward compatibility with memory.jsonl
        """
        self.legacy_compat = legacy_compat
        self.legacy_path = Path.home() / ".openclaw" / "workspace" / "memory" / "memory.jsonl"
        
        # Define agent stores
        self.agent_stores = {
            "@main": Path.home() / ".openclaw" / "workspace" / "memory" / "main" / "episodic.jsonl",
            "@intel": Path.home() / ".openclaw" / "workspace" / "memory" / "intel" / "episodic.jsonl",
            "@ops": Path.home() / ".openclaw" / "workspace" / "memory" / "ops" / "episodic.jsonl",
            "@comms": Path.home() / ".openclaw" / "workspace" / "memory" / "comms" / "episodic.jsonl",
            "@sentinel": Path.home() / ".openclaw" / "workspace" / "memory" / "sentinel" / "episodic.jsonl",
        }
    
    def route_write(self, agent: str, operation: str, content: str, 
                    meta: Optional[Dict] = None) -> Dict:
        """
        Route a write operation to the correct agent store.
        
        Args:
            agent: Agent identifier
            operation: Operation type (retrieve, write, execute, search, format)
            content: Event description
            meta: Optional metadata
        
        Returns:
            Result dict with entry and success status
        """
        # Validate agent
        if agent not in self.agent_stores:
            return {
                "success": False,
                "error": f"Unknown agent: {agent}",
            }
        
        # Create agent directory
        self.agent_stores[agent].parent.mkdir(parents=True, exist_ok=True)
        
        # Write to agent's store
        entry = write_episode(agent, content, meta or {})
        
        # Optionally write to legacy store (deprecated but still active)
        if self.legacy_compat:
            legacy_entry = {
                "agent": agent,
                "type": operation,
                "ts": entry["ts"],
                "datetime": entry["datetime"],
                "content": content,
            }
            if meta:
                legacy_entry["meta"] = meta
            
            with open(self.legacy_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(legacy_entry, ensure_ascii=False) + "\n")
        
        return {
            "success": True,
            "entry": entry,
            "path": self.agent_stores[agent],
        }
    
    def route_retrieve(self, agent: str, limit: int = 10) -> List[Dict]:
        """
        Retrieve episodes from an agent's store.
        
        Args:
            agent: Agent identifier
            limit: Maximum entries
        
        Returns:
            List of episode entries
        """
        return read_agent_episodes(agent, limit=limit)
    
    def route_read_all(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """
        Read all agent stores for cross-agent context.
        
        Args:
            limit: Maximum entries per agent
        
        Returns:
            Dict mapping agent -> list of episodes
        """
        return {
            agent: self.route_retrieve(agent, limit=limit)
            for agent in self.agent_stores
        }
    
    def route_vault_write(self, fact: str, agent: str = "@main") -> Dict:
        """
        Write an immutable fact to the shared vault (Qdrant).
        
        Args:
            fact: Fact string (immutable)
            agent: Agent writing (should be @main)
        
        Returns:
            Result dict with point_id
        """
        if agent != "@main":
            return {
                "success": False,
                "error": "Only @main can write to shared vault",
            }
        
        # In production: Use qdrant-client to upsert Point ID 1
        # For now, simulate with JSON file
        
        vault_path = Path.home() / ".openclaw" / "workspace" / "memory" / "vault.json"
        
        # Load existing vault
        vault = []
        if vault_path.exists():
            with open(vault_path, "r", encoding="utf-8") as f:
                vault = json.load(f)
        
        # Create/upsert Point ID 1
        point = {
            "id": 1,
            "vector": [],
            "payload": {
                "fact": fact,
                "immutable": True,
                "updated_by": agent,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        }
        
        # Remove old entry if exists
        vault = [p for p in vault if p.get("id") != 1]
        vault.append(point)
        
        # Save vault
        with open(vault_path, "w", encoding="utf-8") as f:
            json.dump(vault, f, ensure_ascii=False)
        
        return {
            "success": True,
            "point_id": 1,
            "fact": fact,
        }
    
    def route_vault_read(self) -> List[Dict]:
        """
        Read from shared vault.
        
        Returns:
            List of vault points
        """
        vault_path = Path.home() / ".openclaw" / "workspace" / "memory" / "vault.json"
        
        if not vault_path.exists():
            return []
        
        with open(vault_path, "r", encoding="utf-8") as f:
            return json.load(f)


def main():
    """Demo the memory router."""
    router = MemoryRouter(legacy_compat=True)
    
    print("=== Memory Router v1 Demo ===\n")
    
    # Write from @intel
    print("1. @intel searches Tavily:")
    result = router.route_write(
        agent="@intel",
        operation="search",
        content="Searched tavily for 'LLM optimization techniques'",
        meta={"source": "tavily_search", "query": "LLM optimization"}
    )
    print(f"   Success: {result['success']}")
    
    # Write from @ops
    print("\n2. @ops executes code:")
    result = router.route_write(
        agent="@ops",
        operation="execute",
        content="Ran python3 script.py to generate context manager",
        meta={"source": "exec", "exit_code": 0}
    )
    print(f"   Success: {result['success']}")
    
    # Write from @comms
    print("\n3. @comms formats report:")
    result = router.route_write(
        agent="@comms",
        operation="format",
        content="Formatted final report with markdown headers",
        meta={"source": "format", "format_type": "markdown"}
    )
    print(f"   Success: {result['success']}")
    
    # Read from @main
    print("\n4. @main reads @intel's search results:")
    episodes = router.route_retrieve("@intel", limit=3)
    print(f"   Retrieved {len(episodes)} episodes from @intel")
    
    # Read all stores
    print("\n5. @main reads all agent stores:")
    all_stores = router.route_read_all(limit=2)
    for agent, episodes in all_stores.items():
        print(f"   {agent}: {len(episodes)} episodes")
    
    # Vault write
    print("\n6. @main writes immutable fact to vault:")
    result = router.route_vault_write(
        fact="qwen3.5:9b deployed on RTX 4070 Super (8.5GB VRAM reserved)",
        agent="@main"
    )
    print(f"   Point ID: {result['point_id']}")
    
    # Vault read
    print("\n7. @intel reads shared vault:")
    vault = router.route_vault_read()
    for point in vault:
        print(f"   Fact: {point['payload'].get('fact', '')}")
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()
