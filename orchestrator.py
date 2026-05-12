#!/usr/bin/env python3
"""
pentagon_orchestrator.py

Unified interface for Pentagon Team with SPG at the core.

Architecture:
Memory Layer (episodic + semantic)
 ↓
Retrieval System (with SPG pressure gates)
 ↓
System Pressure Governor (NEW CORE)
 ↓
Agent Execution Layer (PCG-controlled)
 ↓
Compression Engine (pressure-triggered)
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from spg import get_sp_governor
from search_integration import init_pressure_aware_search
from pcg import init_pressure_controlled_gateway
from memory_router import init_pressure_aware_routing

class PentagonOrchestrator:
    """
    Pentagon System Orchestrator with SPG as the unified control layer.
    
    All operations check SPG pressure before executing.
    """
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.spg = get_sp_governor()
        self.search = init_pressure_aware_search(workspace)
        self.pcg = init_pressure_controlled_gateway(workspace)
        self.router = init_pressure_aware_routing(workspace)
        self._startup_report = None
    
    def initialize(self) -> Dict[str, Any]:
        """Initialize orchestrator with Vault-Pulse."""
        try:
            # Vault-Pulse: Check heartbeat
            import requests
            vault_response = requests.get("http://localhost:6333/collections/pentagon_brain/points/1", timeout=5)
            if vault_response.status_code == 200:
                heartbeat = vault_response.json()
                self._startup_report = {
                    "status": "healthy",
                    "vault_response": heartbeat.get("payload", {}),
                    "spg_signal": self.spg.get_pressure_signal(),
                    "recommendation": self.spg.get_recommendation(),
                }
                return self._startup_report
        except Exception as e:
            self._startup_report = {"status": "vault_unreachable", "error": str(e)}
        
        return self._startup_report or {"status": "initialized"}
    
    def handle_user_request(self, request: str) -> Dict[str, Any]:
        """
        Handle user request with full SPG pipeline.
        
        Flow:
        1. Check SPG pressure
        2. Route request via memory_router
        3. Execute search via pressure-aware search
        4. Schedule tasks via PCG
        5. Compress if pressure warrants
        """
        # Step 1: Check SPG pressure
        pressure_data = self.spg.calculate_pressure()
        signal = self.spg.get_pressure_signal()
        
        if pressure_data["zone"] in ["CRITICAL", "EMERGENCY"]:
            return {
                "status": "pressure_too_high",
                "zone": pressure_data["zone"],
                "signal": signal,
                "recommendation": self.spg.get_recommendation(),
            }
        
        # Step 2: Route request
        if "search" in request.lower() or "find" in request.lower():
            routing_decision = self.router.route_search(request)
            if routing_decision["status"] == "denied_emergency":
                return routing_decision
            # Step 3: Execute search
            search_result = self.search.execute_search(request, max_results=5)
            return {
                "status": "search_executed",
                "routing_decision": routing_decision,
                "search_results": search_result.get("final_results", []),
            }
        elif "compress" in request.lower() or "optimize" in request.lower():
            return self._handle_compression(request)
        elif "schedule" in request.lower() or "run" in request.lower():
            return self.pcg.schedule_task(request)
        else:
            return {
                "status": "general_response",
                "signal": signal,
                "recommendation": self.spg.get_recommendation(),
            }
    
    def _handle_compression(self, request: str) -> Dict[str, Any]:
        """Handle compression requests based on pressure."""
        pressure_data = self.spg.calculate_pressure()
        
        if pressure_data["zone"] in ["THROTTLE", "CRITICAL", "EMERGENCY"]:
            actions = pressure_data["actions"]
            return {
                "status": "compression_triggered",
                "zone": pressure_data["zone"],
                "actions": actions,
                "recommendation": self.spg.get_recommendation(),
            }
        else:
            return {
                "status": "compression_not_needed",
                "zone": pressure_data["zone"],
                "recommendation": "System pressure nominal. No compression required.",
            }
    
    def export_status(self, filename: Optional[str] = None) -> str:
        """Export system status with SPG metrics."""
        if filename is None:
            filename = f"{self.workspace}/metrics/spg_status_{int(time.time())}.json"
        
        pressure_data = self.spg.calculate_pressure()
        status = {
            "timestamp": time.time(),
            "pressure_index": pressure_data["pressure_index"],
            "zone": pressure_data["zone"],
            "signal": pressure_data["actions"],
            "recommendation": self.spg.get_recommendation(),
            "metrics": {
                "context_usage": pressure_data["context_usage"],
                "retrieval_rate": pressure_data["retrieval_rate"],
                "agent_load": pressure_data["agent_load"],
                "compression_backlog": pressure_data["compression_backlog"],
                "memory_growth_rate": pressure_data["memory_growth_rate"],
            },
        }
        
        with open(filename, "w") as f:
            json.dump(status, f, indent=2)
        
        return filename


def main():
    """Main entry point for Pentagon Orchestrator."""
    orchestrator = PentagonOrchestrator("/home/jason2ykk/.openclaw/workspace")
    orchestrator.initialize()
    
    print("🚀 Pentagon Orchestrator Initialized\n")
    print(f"🧠 SYSTEM PRESSURE: {orchestrator.spg.get_pressure_signal()}")
    print(f"Recommendation: {orchestrator.spg.get_recommendation()}\n")
    
    # Interactive loop
    print("\nCommands: search, compress, schedule, health, status, quit\n")
    
    while True:
        try:
            cmd = input("Enter command: ")
            
            if cmd.strip().lower() in ["quit", "exit", "q"]:
                break
            
            elif cmd.strip().lower() == "health":
                print(orchestrator.pcg.health_check())
            
            elif cmd.strip().lower() in ["search", "find"]:
                query = input("Query: ")
                result = orchestrator.handle_user_request(query)
                print(json.dumps(result, indent=2))
            
            elif cmd.strip().lower() in ["compress", "optimize"]:
                result = orchestrator._handle_compression(cmd)
                print(json.dumps(result, indent=2))
            
            else:
                print(orchestrator.handle_user_request(cmd))
                
        except EOFError:
            break


if __name__ == "__main__":
    main()
