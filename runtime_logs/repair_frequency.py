#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repair Frequency Tracker
Monitors repair operations for long-horizon pattern detection
"""

import json
from pathlib import Path
from datetime import datetime

class RepairFrequencyTracker:
    """Track repair frequency and patterns"""
    
    def __init__(self, log_dir: str = "/home/jason2ykk/.openclaw/workspace/runtime_logs"):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "repair_frequency.log"
    
    def record_repair(self, repair_type: str, reason: str):
        """Record a repair operation"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "repair_type": repair_type,
            "reason": reason,
            "operator": "auto" if reason.startswith("auto:") else "manual"
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def get_repair_rate(self, window_minutes: int = 60) -> float:
        """Get repair rate (repairs per minute) for time window"""
        if not self.log_file.exists():
            return 0.0
        
        # Parse last window_minutes worth of repairs
        cutoff = datetime.now() - timedelta(minutes=window_minutes)
        
        repairs = 0
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                repair_time = datetime.fromisoformat(data["timestamp"])
                if repair_time > cutoff:
                    repairs += 1
        
        return repairs / window_minutes
    
    def get_repair_types(self) -> dict:
        """Get breakdown of repair types"""
        if not self.log_file.exists():
            return {}
        
        types = {}
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                rtype = data["repair_type"]
                types[rtype] = types.get(rtype, 0) + 1
        
        return types
    
    def get_repair_reasons(self) -> dict:
        """Get breakdown of repair reasons"""
        if not self.log_file.exists():
            return {}
        
        reasons = {}
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                reason = data["reason"]
                reasons[reason] = reasons.get(reason, 0) + 1
        
        return reasons

def main():
    print("🔧 Repair Frequency Tracker Ready")
    print("Monitoring: repair operations, frequency, patterns")
    return RepairFrequencyTracker()

if __name__ == "__main__":
    main()
