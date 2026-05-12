#!/usr/bin/env python3
"""
memory_router.py - Agent Memory Routing Layer with SPG Integration

Integrates:
- LTM v1 storage layer (episodic + semantic)
- SPG pressure gates
- Agent memory logs (agents/*.jsonl)

Routes:
1. Search → Tavily
2. Code → Ops
3. Message → Comms
4. Memory check → Sentinel

Pressure-gated routing:
- SAFE/EARLY: All routes available
- THROTTLE: Route only to essential agents
- CRITICAL: Route to sentinel only
- EMERGENCY: Deny routing
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from spg import get_sp_governor
from memory_v1 import init_memory_system
from compressor_ltm import LTMCompressor

class MemoryRouter:
    """
    Memory router with SPG pressure integration.
    
    Architecture:
    Memory Layer (LTM v1 + Agent Logs)
    ↓
    Retrieval System (with SPG gates)
    ↓
    Routing Logic (pressure-gated)
    ↓
    Execution (PCG-controlled)
    """
    
    AGENT_TYPES = {
        "search": ("tavily_search", "Tavily"),
        "code": ("ops", "Execution Ops"),
        "message": ("comms", "Communications"),
        "memory_check": ("sentinel", "Sentinel"),
    }
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.memory = init_memory_system(workspace)
        self.spg = get_sp_governor()
        self.compressor = LTMCompressor(self.workspace / "episodic.jsonl")
        self.agents_dir = self.workspace / "agents"
        self._last_routing_decision = None
    
    def get_pressure_signal(self) -> str:
        """Get current SPG pressure signal."""
        return self.spg.get_pressure_signal()
    
    def get_pressure_zone(self) -> str:
        """Get current SPG pressure zone."""
        pressure_data = self.spg.calculate_pressure()
        return pressure_data["zone"]
    
    def check_memory_backlog(self) -> Dict[str, Any]:
        """Check memory backlog for compression trigger."""
        episodic_lines = self.memory.get_episodic_count()
        semantic_lines = self.memory.get_semantic_count()
        
        return {
            "episodic_lines": episodic_lines,
            "semantic_lines": semantic_lines,
            "compression_needed": episodic_lines >= 3000,
            "threshold": 3000,
        }
    
    def compress_memory(self) -> Dict[str, Any]:
        """Compress memory if pressure warrants."""
        pressure_data = self.spg.calculate_pressure()
        result = self.compressor.run_pressure_check(pressure_data["pressure_index"])
        
        return {
            "status": "compression_done" if result.get("status") in ["compressed", "pressure_triggered"] else "monitoring",
            "result": result,
        }
    
    def route_search(self, query: str) -> Dict[str, Any]:
        """Route search query to Tavily."""
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        if zone == "EMERGENCY":
            return {
                "status": "denied_emergency",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny search requests",
            }
        
        elif zone in ["CRITICAL", "THROTTLE"]:
            # Throttle search results
            return {
                "status": "routed_throttled",
                "zone": zone,
                "signal": signal,
                "query": query,
                "warning": "Search throttled due to system pressure",
            }
        
        else:
            # Full routing
            return {
                "status": "routed",
                "zone": zone,
                "signal": signal,
                "query": query,
                "agent": "tavily_search",
            }
    
    def route_code(self, code_request: str) -> Dict[str, Any]:
        """Route code request to @ops."""
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        if zone == "EMERGENCY":
            return {
                "status": "denied_emergency",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny code execution",
            }
        
        elif zone in ["CRITICAL", "THROTTLE"]:
            return {
                "status": "routed_throttled",
                "zone": zone,
                "signal": signal,
                "request": code_request,
                "warning": "Code execution throttled",
            }
        
        else:
            return {
                "status": "routed",
                "zone": zone,
                "signal": signal,
                "request": code_request,
                "agent": "ops",
            }
    
    def route_message(self, message: str) -> Dict[str, Any]:
        """Route message to @comms."""
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        if zone == "EMERGENCY":
            return {
                "status": "denied_emergency",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny messaging",
            }
        
        else:
            return {
                "status": "routed",
                "zone": zone,
                "signal": signal,
                "message": message,
                "agent": "comms",
            }
    
    def route_memory_check(self, memory_type: str = "episodic") -> Dict[str, Any]:
        """Route memory check to @sentinel."""
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        if zone == "EMERGENCY":
            return {
                "status": "denied_emergency",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny memory checks",
            }
        
        else:
            return {
                "status": "routed",
                "zone": zone,
                "signal": signal,
                "memory_type": memory_type,
                "agent": "sentinel",
            }
    
    def route_general(self, request: str) -> Dict[str, Any]:
        """Route general request to appropriate agent."""
        request_lower = request.lower()
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        # Check pressure first
        if zone == "EMERGENCY":
            return {
                "status": "denied_emergency",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny general request",
            }
        
        # Route based on request type
        if "search" in request_lower or "find" in request_lower:
            return self.route_search(request)
        elif "code" in request_lower or "run" in request_lower or "write" in request_lower:
            return self.route_code(request)
        elif "message" in request_lower or "send" in request_lower:
            return self.route_message(request)
        elif "memory" in request_lower or "check" in request_lower:
            return self.route_memory_check()
        else:
            return {
                "status": "routed_general",
                "zone": zone,
                "signal": signal,
                "request": request,
                "agent": "intel",  # Default to intel
            }
    
    def get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """Get state of a specific agent."""
        agents_dir = self.agents_dir / agent_id
        if not agents_dir.exists():
            return {"agent": agent_id, "exists": False}
        
        # Check if agent is active
        active_file = agents_dir / "active.jsonl"
        active_status = "active" if active_file.exists() else "inactive"
        
        return {
            "agent": agent_id,
            "exists": True,
            "active_status": active_status,
            "path": str(agents_dir),
        }
    
    def get_active_agents(self) -> List[str]:
        """Get list of active agents."""
        agents = []
        if self.agents_dir.exists():
            for agent_dir in self.agents_dir.iterdir():
                if agent_dir.is_dir():
                    active_file = agent_dir / "active.jsonl"
                    if active_file.exists():
                        with open(active_file) as f:
                            for line in f:
                                agent = json.loads(line)
                                agents.append(agent.get("id"))
        return agents
    
    def health_check(self) -> Dict[str, Any]:
        """Perform system health check."""
        pressure_data = self.spg.calculate_pressure()
        memory_status = self.check_memory_backlog()
        active_agents = self.get_active_agents()
        
        return {
            "timestamp": time.time(),
            "pressure": {
                "index": pressure_data["pressure_index"],
                "zone": pressure_data["zone"],
                "signal": self.get_pressure_signal(),
            },
            "memory": {
                "episodic_lines": memory_status["episodic_lines"],
                "semantic_lines": memory_status["semantic_lines"],
                "compression_needed": memory_status["compression_needed"],
            },
            "agents": {
                "active_count": len(active_agents),
                "agent_ids": active_agents,
            },
            "recommendation": self.spg.get_recommendation(),
        }


def init_pressure_aware_routing(workspace: Optional[str] = None) -> MemoryRouter:
    """Initialize pressure-aware memory router."""
    return MemoryRouter(workspace=workspace)


if __name__ == "__main__":
    router = init_pressure_aware_routing("/home/jason2ykk/.openclaw/workspace")
    signal = router.get_pressure_signal()
    
    print("🧠 Pentagon Memory Router Initialized")
    print(f"Initial Pressure Signal: {signal}")
    print("\nCommands: search, route, health, agents, quit\n")
    
    while True:
        try:
            cmd = input("Enter command: ")
            
            if cmd.strip().lower() in ["quit", "exit", "q"]:
                break
            
            elif cmd.strip().lower() == "health":
                print(json.dumps(router.health_check(), indent=2))
            
            elif cmd.strip().lower() == "agents":
                print(json.dumps({"active_agents": router.get_active_agents()}, indent=2))
            
            elif cmd.strip().lower().startswith("search "):
                query = cmd.strip().replace("search ", "")
                result = router.route_search(query)
                print(json.dumps(result, indent=2))
            
            else:
                print(json.dumps(router.route_general(cmd), indent=2))
                
        except EOFError:
            break
