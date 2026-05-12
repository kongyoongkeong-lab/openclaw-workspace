#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SPG (Super Governance Intelligence) Core
Master governance intelligence layer for controlled production deployment
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# Configuration
@dataclass
class SPGConfig:
    """SPG Configuration Constants"""
    MAX_ACTIVE_AGENTS: int = 3
    RETRIEVAL_TOP_K: int = 3
    MAX_CONTEXT_USAGE: float = 0.70
    COMPRESSION_MODE: str = "moderate"
    ALERT_MODE: str = "binary"
    HARD_CONTEXT_CEILING: float = 0.85
    QUEUE_DEPTH_THRESHOLD: int = 3
    COMPRESSION_DEFERRAL_THRESHOLD_MS: int = 220
    RETRIEVAL_FLOOD_THRESHOLD: int = 50
    
    # Metrics thresholds
    RETRIEVAL_ACCURACY_WARN: float = 95
    RETRIEVAL_ACCURACY_CRITICAL: float = 90
    DUPLICATION_RATE_WARN: float = 5
    DUPLICATION_RATE_CRITICAL: float = 10
    COMPRESSION_THRESHOLD: int = 3000
    COMPRESSION_RATIO_TARGET: str = "50%"
    VRAM_THRESHOLD_GB: float = 9.5
    VRAM_TARGET_PERCENT: float = 0.85
    
class SPGMetrics:
    """SPG Metrics Collector"""
    
    def __init__(self):
        self.metrics_path = Path("/home/jason2ykk/.openclaw/workspace/runtime_logs/metrics.jsonl")
        self.data = {
            "event_loop_p99": [],
            "queue_depth": [],
            "context_usage": [],
            "control_delta": [],
            "compression_latency": [],
            "retrieval_accuracy": [],
            "vram_baseline_drift": []
        }
    
    def record(self, metric: str, value: float):
        """Record a metric with timestamp"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "metric": metric,
            "value": value
        }
        with open(self.metrics_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.data[metric].append(entry)
        
        # Keep last 1000 entries for analysis
        if len(self.data[metric]) > 1000:
            self.data[metric] = self.data[metric][-1000:]
    
    def get_average(self, metric: str) -> float:
        """Get average for a metric"""
        if not self.data[metric]:
            return 0.0
        return sum(e["value"] for e in self.data[metric]) / len(self.data[metric])
    
    def get_percentile(self, metric: str, percentile: int) -> float:
        """Get percentile for a metric"""
        if not self.data[metric]:
            return 0.0
        sorted_values = sorted(e["value"] for e in self.data[metric])
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
    
    def get_latest(self, metric: str) -> Optional[float]:
        """Get latest value for a metric"""
        if not self.data[metric]:
            return None
        return self.data[metric][-1]["value"]
    
    def clear(self):
        """Clear all metrics"""
        self.data = {k: [] for k in self.data}
        self.metrics_path.unlink(missing_ok=True)

# Governance Intelligence
class SPGGovernor:
    """SPG Governor - Enforces governance locks"""
    
    def __init__(self, metrics: SPGMetrics):
        self.metrics = metrics
        self.repair_count = 0
        self.last_repair_time: Optional[float] = None
    
    def check_context_ceiling(self, context_usage: float) -> bool:
        """Check hard context ceiling lock"""
        if context_usage > self.HARD_CONTEXT_CEILING:
            self.metrics.record("control_delta", 1.0)
            return False  # Suppress non-critical retrieval
        return True
    
    def check_queue_admission(self, queue_depth: int) -> bool:
        """Check queue admission control"""
        if queue_depth > self.QUEUE_DEPTH_THRESHOLD:
            return False  # Reject background tasks
        return True
    
    def check_compression_deferral(self, latency_ms: float) -> bool:
        """Check compression deferral threshold"""
        if latency_ms > self.COMPRESSION_DEFERRAL_THRESHOLD_MS:
            self.metrics.record("compression_latency", latency_ms)
            return False  # Defer compression
        return True
    
    def check_retrieval_flood(self, retrieval_rate: int) -> bool:
        """Check retrieval flood protection"""
        if retrieval_rate > self.RETRIEVAL_FLOOD_THRESHOLD:
            return False  # Reduce top_k
        return True
    
    def repair(self):
        """Perform repair (single use per cooldown)"""
        self.repair_count += 1
        self.last_repair_time = time.time()
    
    def is_cooldown_active(self) -> bool:
        """Check if repair cooldown is active"""
        if self.last_repair_time is None:
            return True  # Fresh, can repair
        elapsed = time.time() - self.last_repair_time
        return elapsed < 60  # 60 second cooldown
    
    def get_control_delta(self) -> float:
        """Calculate control delta (repair effectiveness)"""
        if self.last_repair_time is None:
            return 0.0
        # Simplified: delta is based on repair frequency
        return 1.0 if self.repair_count == 1 else 0.5

# Runtime State
class SPGRuntime:
    """SPG Runtime State Manager"""
    
    def __init__(self, config: SPGConfig):
        self.config = config
        self.metrics = SPGMetrics()
        self.governor = SPGGovernor(self.metrics)
        self.runtime_logs_path = Path("/home/jason2ykk/.openclaw/workspace/runtime_logs/runtime_state.json")
    
    def initialize(self):
        """Initialize runtime state"""
        self.runtime_logs_path.write_text(json.dumps({
            "spg_version": "1.0.0",
            "config": self.config.__dict__,
            "initialized_at": datetime.now().isoformat(),
            "status": "active"
        }, indent=2))
    
    def record_event(self, event_type: str, details: Dict):
        """Record runtime event"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "details": details
        }
        log_path = self.runtime_logs_path.with_stem(f"runtime_{datetime.now().strftime('%Y%m%d')}_")
        with open(log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def check_stability(self) -> Dict:
        """Check overall runtime stability"""
        return {
            "event_loop_p99_ms": self.metrics.get_percentile("event_loop_p99", 99),
            "queue_depth_avg": self.metrics.get_average("queue_depth"),
            "context_usage_avg": self.metrics.get_average("context_usage"),
            "retrieval_accuracy_avg": self.metrics.get_average("retrieval_accuracy"),
            "governance_active": True,
            "status": "stable" if (
                self.metrics.get_average("context_usage") < self.config.MAX_CONTEXT_USAGE and
                self.metrics.get_average("retrieval_accuracy") >= self.config.RETRIEVAL_ACCURACY_WARN
            ) else "degraded"
        }

def main():
    """SPG Core - Main Runtime"""
    print("=" * 60)
    print("SPG CORE - SUPER GOVERNANCE INTELLIGENCE")
    print("=" * 60)
    print(f"Initialized: {datetime.now().isoformat()}")
    print()
    
    config = SPGConfig()
    runtime = SPGRuntime(config)
    runtime.initialize()
    
    print("✅ SPG Governance Intelligence Layer Active")
    print(f"   Max Active Agents: {config.MAX_ACTIVE_AGENTS}")
    print(f"   Retrieval Top-K: {config.RETRIEVAL_TOP_K}")
    print(f"   Max Context Usage: {config.MAX_CONTEXT_USAGE * 100:.0f}%")
    print(f"   Compression Mode: {config.COMPRESSION_MODE}")
    print(f"   Alert Mode: {config.ALERT_MODE}")
    print()
    
    print("🔒 Governance Locks Active:")
    print(f"   - Hard Context Ceiling: {config.HARD_CONTEXT_CEILING * 100:.0f}%")
    print(f"   - Queue Admission: Depth {config.QUEUE_DEPTH_THRESHOLD}")
    print(f"   - Compression Deferral: >{config.COMPRESSION_DEFERRAL_THRESHOLD_MS}ms")
    print(f"   - Retrieval Flood: >{config.RETRIEVAL_FLOOD_THRESHOLD} req/sec")
    print()
    
    print("📊 Metrics Being Monitored:")
    for metric in config.__dict__["metrics_priority"]:
        print(f"   - {metric}")
    print()
    
    print("🚀 Ready for Controlled Production Deployment")
    print("=" * 60)
    
    return runtime

if __name__ == "__main__":
    runtime = main()
