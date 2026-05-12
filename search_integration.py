#!/usr/bin/env python3
"""
search_integration.py - Web Search Integration Layer for Pentagon Agents

Connects search_protocol to Pentagon agents via memory_router.

Usage:
1. Agent detects search need → calls search_protocol
2. MemoryRouter routes to search_protocol
3. SearchProtocol executes chain
4. Results returned to agent
"""

from search_protocol import init_pressure_aware_search
from memory_router import init_pressure_aware_routing

class SearchIntegration:
    """
    Web search integration layer for Pentagon agents.
    
    Integration flow:
    1. Agent requests search → MemoryRouter
    2. MemoryRouter checks SPG pressure
    3. If allowed → search_protocol
    4. Results → Agent
    """
    
    def __init__(self, workspace: str):
        self.workspace = workspace
        self.search = init_pressure_aware_search(workspace)
        self.router = init_pressure_aware_routing(workspace)
    
    def agent_search(self, agent_id: str, query: str) -> dict:
        """Agent-triggered search."""
        signal = self.search.protocol.get_pressure_signal()
        zone = self.search.protocol.get_pressure_zone()
        
        if zone == "EMERGENCY":
            return {
                "agent": agent_id,
                "status": "denied",
                "signal": signal,
                "zone": zone,
                "reason": "EMERGENCY: deny search",
            }
        
        # Execute search
        result = self.search.protocol.execute_full_search(query)
        
        # Log to episodic memory
        self.router.memory.append_episodic({
            "event": f"@{agent_id} search query",
            "query": query,
            "status": result.get("status", "unknown"),
            "zone": zone,
            "results_count": len(result.get("results", [])),
        })
        
        return result
    
    def health_check(self) -> dict:
        """Health check for search integration."""
        return {
            "workspace": self.workspace,
            "search_available": self.search.protocol._tavily_available,
            "tavily_key": "configured" if self.search.protocol._tavily_api_key else "not configured",
            "router_active": self.router is not None,
            "pressure_signal": self.search.protocol.get_pressure_signal(),
        }


def init_search_integration(workspace: str) -> SearchIntegration:
    """Initialize search integration for Pentagon agents."""
    return SearchIntegration(workspace=workspace)


if __name__ == "__main__":
    integration = init_search_integration("/home/jason2ykk/.openclaw/workspace")
    
    print("🔗 Pentagon Search Integration Initialized")
    print(f"Signal: {integration.search.protocol.get_pressure_signal()}\n")
    
    # Example search
    print("Example search:\n")
    result = integration.agent_search("intel", "What is the capital of France?")
    print(f"Result: {result}")
