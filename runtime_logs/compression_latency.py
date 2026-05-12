#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compression Latency Tracker
Measures compression operation timing for long-horizon degradation detection
"""

import json
import time
from pathlib import Path
from datetime import datetime

class CompressionLatencyTracker:
    """Track compression latency for degradation detection"""
    
    def __init__(self, log_dir: str = "/home/jason2ykk/.openclaw/workspace/runtime_logs"):
        self.log_dir = Path(log_dir)
        self.log_file = self.log_dir / "compression_latency.log"
        self.baseline_ms = None
        self.degradation_threshold_pct = 0.5  # 50% increase triggers alert
    
    def record_operation(self, lines_compressed: int, latency_ms: float):
        """Record a compression operation"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "lines_compressed": lines_compressed,
            "latency_ms": latency_ms,
            "latency_per_line_ms": latency_ms / max(lines_compressed, 1)
        }
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        
        # Update baseline if first record
        if self.baseline_ms is None:
            self.baseline_ms = latency_ms
            print(f"🔧 Baseline compression latency: {latency_ms:.2f}ms")
        
        # Check for degradation
        if self.baseline_ms and latency_ms > self.baseline_ms * (1 + self.degradation_threshold_pct):
            print(f"⚠️ Compression latency elevated: {latency_ms:.2f}ms (baseline: {self.baseline_ms:.2f}ms)")
            
    def get_avg_latency(self) -> float:
        """Get average compression latency"""
        if not self.log_file.exists():
            return 0.0
        
        latencies = []
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                latencies.append(data["latency_ms"])
        
        return sum(latencies) / len(latencies) if latencies else 0.0
    
    def get_p99_latency(self) -> float:
        """Get 99th percentile latency"""
        latencies = []
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                latencies.append(data["latency_ms"])
        
        if not latencies:
            return 0.0
        
        sorted_latencies = sorted(latencies)
        index = int(len(sorted_latencies) * 0.99)
        return sorted_latencies[min(index, len(sorted_latencies) - 1)]

def main():
    print("🔧 Compression Latency Tracker Ready")
    print("Monitoring: compression operations, latency, degradation")
    print()
    print("Usage: Call record_operation(lines, latency_ms) after each compression")
    return CompressionLatencyTracker()

if __name__ == "__main__":
    main()
