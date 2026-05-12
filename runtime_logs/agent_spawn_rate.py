#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Spawn Rate Tracker
Monitors agent creation/destruction rates for stability analysis
"""

import json
from pathlib import Path
from datetime import datetime

class AgentSpawnRateTracker:
    """Track agent spawn/destruction rates"""
    
    def __init__(self, log_dir: str = "/home/jason2ykk/.openclaw/workspace/runtime_logs"):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "agent_spawn_rate.log"
    
    def record_spawn(self, agent_id: str, reason: str):
        """Record agent spawn event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "spawn",
            "agent_id": agent_id,
            "reason": reason
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def record_destroy(self, agent_id: str, reason: str):
        """Record agent destruction event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "destroy",
            "agent_id": agent_id,
            "reason": reason
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_spawn_rate(self, window_minutes: int = 60) -> float:
        """Get agent spawn rate (spawns per minute)"""
        if not self.log_file.exists():
            return 0.0
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        spawns = 0
        
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                if data["action"] == "spawn":
                    spawn_time = datetime.fromisoformat(data["timestamp"])
                    if spawn_time > cutoff:
                        spawns += 1
        
        return spawns / window_minutes
    
    def get_destruction_rate(self, window_minutes: int = 60) -> float:
        """Get agent destruction rate (destructions per minute)"""
        if not self.log_file.exists():
            return 0.0
        
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        destructions = 0
        
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                if data["action"] == "destroy":
                    destroy_time = datetime.fromisoformat(data["timestamp"])
                    if destroy_time > cutoff:
                        destructions += 1
        
        return destructions / window_minutes
    
    def get_agent_turnover_rate(self) -> float:
        """Get net agent turnover rate (spawns - destructions) per minute"""
        spawns = self.get_spawn_rate()
        destructions = self.get_destruction_rate()
        return spawns - destructions
    
    def get_active_agents(self) -> dict:
        """Get breakdown of agent types spawned"""
        if not self.log_file.exists():
            return {}
        
        agents = {}
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                if data["action"] == "spawn":
                    agent = data["agent_id"]
                    agents[agent] = agents.get(agent, 0) + 1
        
        return agents

def main():
    print("🤖 Agent Spawn Rate Tracker Ready")
    print("Monitoring: agent creation/destruction rates, turnover")
    return AgentSpawnRateTracker()

if __name__ == "__main__":
    main()
