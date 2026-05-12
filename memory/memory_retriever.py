#!/usr/bin/env python3
"""
memory_retriever.py — Isolated Retrieval Orchestrator

Retrieves from agent-specific stores only (NOT global memory.jsonl)
Enforces strict isolation boundaries
"""

import sys
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_router import read_agent_memory, read_shared_vault
from intel.search_retriever import IntelRetriever
from ops.exec_retriever import OpsRetriever
from comms.output_retriever import CommsRetriever


class IsolatedRetriever:
    """
    隔离检索器 - 每个 agent 只能访问自己的 store + 共享 vault
    
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
    """
    
    def __init__(self, agent: str = None):
        self.agent = agent
        self._retrievers = {
            "intel": IntelRetriever(),
            "ops": OpsRetriever(),
            "comms": CommsRetriever(),
        }
        self._shared_vault = None
    
    def get_retriever(self) -> object:
        """Get agent-specific retriever"""
        if not self.agent:
            self.agent = "intel"  # Default
        return self._retrievers.get(self.agent, self._retrievers["intel"])
    
    def retrieve(self, query: str, query_type: str = None, top_k: int = 5) -> list:
        """
        Isolated retrieval - agent-specific store + shared vault only
        
        Args:
            query: Retrieval query
            query_type: "search" | "execution" | "output" | "semantic"
            top_k: Max total results
    
        Returns:
            List of memory entries (agent store + shared vault)
        """
        retriever = self.get_retriever()
        
        if query_type == "semantic":
            # Only shared vault for semantic queries
            return read_shared_vault(query, top_k=min(top_k, 5))
        else:
            # Agent-specific store + shared vault
            results = retriever.retrieve(query, query_type=query_type or "search", top_k=top_k)
            return results
    
    def retrieve_agent_specific(self, agent: str, query: str, top_k: int = 3) -> list:
        """
        Retrieve from specific agent's store
    
        Args:
            agent: Agent label
            query: Retrieval query
            top_k: Max results
    
        Returns:
            Agent-specific results
        """
        return read_agent_memory(agent, top_k)
    
    def is_outside_scope(self, event: dict) -> bool:
        """
        Check if event is outside agent scope
    
        Args:
            event: Memory entry dict
    
        Returns:
            True if event is outside scope
        """
        agent = event.get("agent", "")
        current_agent = self.agent or "intel"
        
        # Allow: own agent, shared vault, or @main (orchestrator)
        if agent in [current_agent, "vault", "shared", "main"]:
            return False
        return True
    
    def read_other_agents(self, other_agents: list, top_k: int = 2) -> dict:
        """
        Read from multiple agents (controlled cross-agent context)
        Only @main should use this
    
        Args:
            other_agents: List of agents to read
            top_k: Results per agent
    
        Returns:
            Dict mapping agent -> results
        """
        result = {}
        for a in other_agents:
            result[a] = self.retrieve_agent_specific(a, "", top_k=top_k)
        return result


if __name__ == "__main__":
    retriever = IsolatedRetriever(agent="intel")
    
    print("=== Isolated Retriever Test ===")
    
    # Test
    results = retriever.retrieve("Python deployment", query_type="search")
    print(f"\n检索结果 for 'Python deployment':")
    for r in results:
        print(f"  Agent: {r.get('agent')}, Content: {r['content'][:60]}...")
    
    # Test scope check
    print("\n\nScope check:")
    test_event = {"agent": "intel", "content": "Intel search result"}
    print(f"  Intel event in scope: {not retriever.is_outside_scope(test_event)}")
    
    test_event = {"agent": "ops", "content": "Ops exec result"}
    print(f"  Ops event in scope: {not retriever.is_outside_scope(test_event)}")
