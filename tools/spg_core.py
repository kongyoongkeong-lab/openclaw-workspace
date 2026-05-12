#!/usr/bin/env python3
"""
SPG Core - System Pressure Governor
Unified control layer for Pentagon orchestration
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import hashlib

@dataclass
class PressureMetric:
    """Individual pressure component"""
    name: str
    value: float
    weight: float
    description: str

class SystemPressureGovernor:
    """
    System Pressure Governor (SPG)
    Unified control layer merging 5 metrics into system_pressure_index
    """
    
    def __init__(self, memory_path: str = "/home/jason2ykk/.openclaw/workspace/memory"):
        self.memory_path = Path(memory_path)
        self.episodic_path = self.memory_path / "episodic.jsonl"
        self.semantic_path = self.memory_path / "semantic.jsonl"
        
        # Define pressure metrics and weights
        self.metrics = [
            PressureMetric(
                name="context_usage",
                weight=0.3,
                description="Current token usage vs 32.8k limit",
                description="Token usage ratio relative to 32.8k limit"
            ),
            PressureMetric(
                name="retrieval_rate",
                weight=0.2,
                description="Queries/sec from @intel operations",
            ),
            PressureMetric(
                name="agent_load",
                weight=0.2,
                description="Active agents and tool execution count",
            ),
            PressureMetric(
                name="compression_backlog",
                weight=0.2,
                description="Lines in episodic memory since last compression",
            ),
            PressureMetric(
                name="memory_growth_rate",
                weight=0.1,
                description="New lines per minute in memory",
            )
        ]
        
        self.pressure_history: list = []
        self.zones = {
            "SAFE": (0, 0.55),
            "EARLY": (0.55, 0.70),
            "THROTTLE": (0.70, 0.80),
            "CRITICAL": (0.80, 0.90),
            "EMERGENCY": (0.9, 1.0)
        }
    
    def calculate_pressure(self, metrics: Dict[str, float]) -> tuple[float, str]:
        """
        Calculate system pressure index from individual metrics
        Returns: (pressure_index, zone)
        """
        pressure = 0.0
        for metric in self.metrics:
            val = metrics.get(metric.name, 0.0)
            pressure += val * metric.weight
        
        # Clamp to [0, 1]
        pressure = max(0.0, min(1.0, pressure))
        
        # Determine zone
        zone = self._determine_zone(pressure)
        
        return pressure, zone
    
    def _determine_zone(self, pressure: float) -> str:
        """Determine current pressure zone"""
        if pressure <= self.zones["SAFE"][1]:
            return "SAFE"
        elif pressure <= self.zones["EARLY"][1]:
            return "EARLY"
        elif pressure <= self.zones["THROTTLE"][1]:
            return "THROTTLE"
        elif pressure <= self.zones["CRITICAL"][1]:
            return "CRITICAL"
        else:
            return "EMERGENCY"
    
    def get_zone_actions(self, zone: str) -> Dict[str, Any]:
        """Get recommended actions for current zone"""
        actions = {
            "SAFE": {
                "actions": ["normal_ops"],
                "recommendations": ["Continue standard operations", "Monitor pressure trends"],
                "alerts": []
            },
            "EARLY": {
                "actions": ["reduce_retrieval_breadth", "optimize_search_queries"],
                "recommendations": ["Limit @intel query volume", "Combine related searches", "Enable smart caching"],
                "alerts": ["Pressure rising - consider reducing search depth"]
            },
            "THROTTLE": {
                "actions": ["compress_memory", "limit_active_agents"],
                "recommendations": ["Compress episodic entries", "Temporarily suspend non-critical agents", "Increase compression frequency"],
                "alerts": ["Throttling active - compression in progress"]
            },
            "CRITICAL": {
                "actions": ["pause_low_priority_tasks", "emergency_compression"],
                "recommendations": ["Suspend all non-essential operations", "Force immediate compression", "Review recent operations"],
                "alerts": ["Critical pressure - only essential operations allowed"]
            },
            "EMERGENCY": {
                "actions": ["read_only_mode", "flush_excess_memory"],
                "recommendations": ["Switch to read-only memory mode", "Flush oldest episodic entries", "Alert system owner"],
                "alerts": ["EMERGENCY - System at risk of instability"]
            }
        }
        return actions.get(zone, {"actions": [], "recommendations": [], "alerts": ["Unknown zone"]})
    
    def collect_metrics(self) -> Dict[str, float]:
        """Collect current metrics from system state"""
        metrics = {}
        
        # Context usage - estimate from recent session (mock)
        # In production, parse session logs
        metrics["context_usage"] = 0.35  # 32.8k limit * 0.35 usage
        
        # Retrieval rate - parse episodic log
        try:
            recent_ops = 0
            with open(self.episodic_path, 'r') as f:
                lines = f.readlines()
                # Last 100 lines
                recent_lines = lines[-100:]
                recent_ops = len(recent_lines) / 60  # ops per minute
            metrics["retrieval_rate"] = min(1.0, recent_ops / 10)  # Normalize to 0-1
        except Exception as e:
            metrics["retrieval_rate"] = 0.0
        
        # Agent load
        try:
            # Parse active agents from memory
            agent_keys = {f"@intel", f"@ops", f"@comms", f"@sentinel"}
            # Mock - in production would check active sessions
            metrics["agent_load"] = min(1.0, 0.5)  # Moderate load
        except Exception as e:
            metrics["agent_load"] = 0.0
        
        # Compression backlog
        try:
            with open(self.episodic_path, 'r') as f:
                lines = f.readlines()
                metrics["compression_backlog"] = len(lines) / 3000  # Normalize to threshold
        except Exception as e:
            metrics["compression_backlog"] = 0.0
        
        # Memory growth rate
        try:
            # Compare current vs recent checkpoint
            import os
            current_size = os.path.getsize(self.episodic_path)
            metrics["memory_growth_rate"] = min(1.0, current_size / 1000000)  # Normalize
        except Exception as e:
            metrics["memory_growth_rate"] = 0.0
        
        return metrics
    
    def get_pressure_report(self) -> Dict[str, Any]:
        """Generate comprehensive pressure report"""
        metrics = self.collect_metrics()
        pressure, zone = self.calculate_pressure(metrics)
        actions = self.get_zone_actions(zone)
        
        report = {
            "timestamp": time.time(),
            "pressure": round(pressure, 4),
            "zone": zone,
            "metrics": {m.name: round(v, 4) for m, v in self.metrics},
            "actions": actions["actions"],
            "recommendations": actions["recommendations"],
            "alerts": actions["alerts"]
        }
        
        return report
    
    def log_pressure(self, report: Dict[str, Any], log_path: Optional[Path] = None):
        """Log pressure reading to file"""
        if log_path is None:
            log_path = self.memory_path / "pressure.log"
        
        log_entry = json.dumps(report)
        with open(log_path, 'a') as f:
            f.write(log_entry + '\n')
    
    def get_command_recommendations(self) -> str:
        """Generate shell commands for current pressure zone"""
        zone = self.get_zone_actions(self.calculate_pressure(self.collect_metrics())[1])["actions"]
        
        cmd_parts = []
        for action in zone:
            if "compress_memory" in action:
                cmd_parts.append("./compressor_ltm.py compress")
            elif "pause_low_priority_tasks" in action:
                cmd_parts.append("sessions_spawn(runtime=subagent, context=isolated) - pause")
            elif "reduce_retrieval_breadth" in action:
                cmd_parts.append("@intel: reduce_search_depth=2")
            elif "emergency_compression" in action:
                cmd_parts.append("./compressor_ltm.py emergency --force")
        
        if not cmd_parts:
            return "No action required - system in SAFE zone"
        
        return "\n".join(cmd_parts)


if __name__ == "__main__":
    spg = SystemPressureGovernor()
    report = spg.get_pressure_report()
    print(f"System Pressure: {report['pressure']:.2%}")
    print(f"Current Zone: {report['zone']}")
    print(f"\nRecommendations:")
    for rec in report["recommendations"]:
        print(f"  • {rec}")
    print(f"\nAlerts:")
    for alert in report["alerts"]:
        print(f"  ⚠️ {alert}")