#!/usr/bin/env python3
"""
pcg.py - Pressure-Controlled Gateway (PCG)

Integrates SPG into agent scheduling and task dispatching.
Controls:
- Agent selection based on pressure zones
- Task batching for THROTTLE/CRITICAL zones
- Emergency fallback routing
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from spg import get_sp_governor
from sessions_spawn import sessions_spawn

class PressureControlledGateway:
    """
    Gateway that schedules agents based on SPG pressure signals.
    
    Agent Selection by Zone:
    - SAFE: Full parallelism, all agents available
    - EARLY: Reduce parallelism, use most efficient agents
    - THROTTLE: Single-threaded, batch tasks
    - CRITICAL: Serial execution, no parallelism
    - EMERGENCY: Fallback routing only
    """
    
    AGENTS = [
        "intel",  # Research agent
        "ops",    # Execution agent
        "comms",  # Communication agent
        "sentinel",  # Guardian agent
    ]
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.spg = get_sp_governor()
        self._current_session = None
    
    def schedule_task(self, task: str, priority: str = "normal",
                      timeout: int = 300) -> Dict[str, Any]:
        """Schedule task with pressure-aware agent selection."""
        signal = self.spg.get_pressure_signal()
        zone = self.spg.calculate_pressure()["zone"]
        
        # Pressure-gated agent selection
        if zone == "SAFE":
            selected_agents = self.AGENTS
            parallelism = "full"
        elif zone == "EARLY":
            selected_agents = self.AGENTS[:2]  # Limit to 2 agents
            parallelism = "reduced"
        elif zone == "THROTTLE":
            selected_agents = self.AGENTS[:1]  # Single agent
            parallelism = "serial"
        elif zone == "CRITICAL":
            selected_agents = ["sentinel"]  # Only guardian
            parallelism = "minimal"
        elif zone == "EMERGENCY":
            selected_agents = ["sentinel"]  # Read-only fallback
            parallelism = "emergency"
        
        # Spawn sub-agent if in safe/early zones
        result = self._execute_with_parallelism(task, selected_agents, parallelism, timeout)
        
        # Record scheduling decision
        self._log_scheduling_decision({
            "task": task,
            "zone": zone,
            "signal": signal,
            "selected_agents": selected_agents,
            "parallelism": parallelism,
            "timestamp": time.time(),
        })
        
        return {
            "status": "scheduled",
            "task": task,
            "zone": zone,
            "signal": signal,
            "selected_agents": selected_agents,
            "parallelism": parallelism,
            "result": result,
        }
    
    def _execute_with_parallelism(self, task: str, agents: List[str],
                                  parallelism: str, timeout: int) -> Dict[str, Any]:
        """Execute task with pressure-gated parallelism."""
        if parallelism == "full":
            # Spawn all agents in parallel
            results = []
            for agent in agents:
                try:
                    sub = sessions_spawn(
                        task=task,
                        label=f"pentagon_{agent}",
                        runtime="subagent",
                        agentId=agent,
                        timeoutSeconds=timeout,
                    )
                    results.append({"agent": agent, "session": sub.get("sessionKey")})
                except Exception as e:
                    results.append({"agent": agent, "error": str(e)})
            return {"parallel_execution": results}
        
        elif parallelism in ["reduced", "serial"]:
            # Execute sequentially with pressure-aware agent selection
            last_result = None
            for agent in agents:
                try:
                    sub = sessions_spawn(
                        task=task,
                        label=f"pentagon_{agent}",
                        runtime="subagent",
                        agentId=agent,
                        timeoutSeconds=timeout,
                    )
                    last_result = {"agent": agent, "session": sub.get("sessionKey")}
                except Exception as e:
                    last_result = {"agent": agent, "error": str(e)}
            return {"sequential_execution": last_result}
        
        else:
            # Emergency mode: only sentinel
            return {"emergency_mode": {"fallback": "sentinel_only"}}
    
    def batch_tasks(self, tasks: List[str], max_parallel: int = 2) -> Dict[str, Any]:
        """Batch tasks based on pressure zone."""
        zone = self.spg.calculate_pressure()["zone"]
        
        if zone in ["SAFE", "EARLY"]:
            # Full parallelism for safe zones
            return {
                "status": "batched",
                "zone": zone,
                "max_parallel": max_parallel,
                "tasks": tasks,
            }
        
        elif zone == "THROTTLE":
            # Batch with reduced parallelism
            return {
                "status": "batched_throttled",
                "zone": zone,
                "max_parallel": 1,
                "tasks": tasks,
            }
        
        elif zone in ["CRITICAL", "EMERGENCY"]:
            # Single task at a time
            return {
                "status": "single_task_mode",
                "zone": zone,
                "reason": self.spg.get_recommendation(),
                "tasks_queued": tasks,
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check system health based on pressure."""
        pressure_data = self.spg.calculate_pressure()
        
        return {
            "pressure_index": pressure_data["pressure_index"],
            "zone": pressure_data["zone"],
            "safe_agents": len(self.AGENTS) if pressure_data["zone"] in ["SAFE", "EARLY"] else 1,
            "recommendation": self.spg.get_recommendation(),
        }


def init_pressure_controlled_gateway():
    """Initialize pressure-controlled gateway."""
    pgw = PressureControlledGateway("/home/jason2ykk/.openclaw/workspace")
    return pgw


if __name__ == "__main__":
    pgw = init_pressure_controlled_gateway()
    signal = pgw.spg.get_pressure_signal()
    
    print(f"🧠 SYSTEM PRESSURE: {signal}\n")
    
    # Test scheduling
    task = "research latest AI safety reports"
    print(f"Scheduling task: {task}")
    
    result = pgw.schedule_task(task, priority="normal")
    
    print(f"Zone: {result['zone']}")
    print(f"Selected agents: {result['selected_agents']}")
    print(f"Parallelism: {result['parallelism']}")
    print(f"Recommendation: {pgw.spg.get_recommendation()}")
