#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Control Delta Measurement
Measures repair effectiveness and governance intervention impact
"""

import json
from pathlib import Path
from datetime import datetime

class ControlDeltaTracker:
    """Measure control delta (repair effectiveness)"""
    
    def __init__(self, log_dir: str = "/home/jason2ykk/.openclaw/workspace/runtime_logs"):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "control_delta.log"
        self.last_repair_time: float = None
        self.repair_count: int = 0
    
    def record_repair(self, issue_type: str, success: bool):
        """Record a repair operation"""
        self.repair_count += 1
        
        # Calculate control delta
        if self.last_repair_time:
            time_since_repair = datetime.now().timestamp() - self.last_repair_time
            # Delta: effectiveness decays with frequency of repairs
            repair_frequency = self.repair_count / max(time_since_repair, 1)
            control_delta = max(0.0, 1.0 - (repair_frequency * 10))
        else:
            control_delta = 1.0
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_type,
            "success": success,
            "repair_count": self.repair_count,
            "control_delta": round(control_delta, 3),
            "time_since_last_repair_seconds": round(time_since_repair, 2) if self.last_repair_time else None
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        self.last_repair_time = datetime.now().timestamp()
        return control_delta
    
    def get_avg_control_delta(self) -> float:
        """Get average control delta"""
        if not self.log_file.exists():
            return 1.0
        
        deltas = []
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                deltas.append(data["control_delta"])
        
        return sum(deltas) / len(deltas) if deltas else 1.0
    
    def get_repair_frequency(self) -> float:
        """Get repair frequency (repairs per minute)"""
        if not self.log_file.exists():
            return 0.0
        
        repairs = 0
        timestamps = []
        
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                repairs += 1
                timestamps.append(datetime.fromisoformat(data["timestamp"]))
        
        if len(timestamps) < 2:
            return 0.0
        
        duration = (timestamps[-1] - timestamps[0]).total_seconds()
        if duration <= 0:
            return 0.0
        
        return (repairs / duration) * 60  # repairs per minute
    
    def check_repair_oscillation(self) -> bool:
        """Check for repair oscillation (repair → issue → repair loop)"""
        if not self.log_file.exists():
            return False
        
        repairs = []
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                repairs.append({
                    "timestamp": data["timestamp"],
                    "issue_type": data["issue_type"],
                    "success": data["success"]
                })
        
        # Check for oscillation: same issue type repaired repeatedly within short window
        if len(repairs) < 3:
            return False
        
        window_seconds = 5
        oscillation_detected = False
        
        for i in range(len(repairs) - 2):
            current = repairs[i]
            next_repair = repairs[i + 1]
            time_diff = (datetime.fromisoformat(next_repair["timestamp"]) - 
                        datetime.fromisoformat(current["timestamp"])).total_seconds()
            
            if time_diff <= window_seconds and current["issue_type"] == next_repair["issue_type"]:
                oscillation_detected = True
                break
        
        return oscillation_detected

def main():
    print("🎯 Control Delta Measurement Tracker Ready")
    print("Monitoring: repair effectiveness, control delta, oscillation")
    return ControlDeltaTracker()

if __name__ == "__main__":
    main()
