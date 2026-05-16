#!/usr/bin/env python3
"""
Workload Composition Tracker

实时计算每个 event 的 workload regime，用于 conditioning baseline.
"""

import json
import os
from datetime import datetime
from pathlib import Path

class WorkloadComposer:
    """
    为每个 trace event 计算 workload regime.
    
    Regime = f(tool_count, handoff_depth, context_depth)
    """
    
    def __init__(self, workspace: str = "/home/jason2ykk/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.metrics_dir = self.workspace / "memory" / "telemetry"
        self.tracking_dir = self.metrics_dir / "workload_tracking"
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        
        # Bucket thresholds
        self.tool_buckets = {
            "low": (0, 1),
            "medium": (1, 4),
            "high": (4, float("inf"))
        }
        self.handoff_buckets = {
            "1-2": (0, 2),
            "3-4": (2, 4),
            "5+": (4, float("inf"))
        }
        self.context_buckets = {
            "0-30%": (0, 30),
            "30-70%": (30, 70),
            "70-100%": (70, 100)
        }
    
    def compute_regime(self, tool_count: int, handoff_depth: int, context_idle_pct: float) -> dict:
        """
        计算 event 的 regime conditioning key.
        
        Args:
            tool_count: 当前 event 的活跃 tool 数量
            handoff_depth: 当前 event 的 agent handoff 深度
            context_idle_pct: context idle 百分比
            
        Returns:
            {"bucket": {...}, "regime_id": "unique_id"}
        """
        # Determine tool bucket
        tool_key = "low"
        for key, (lo, hi) in self.tool_buckets.items():
            if lo <= tool_count < hi:
                tool_key = key
                break
        
        # Determine handoff bucket
        handoff_key = "1-2"
        for key, (lo, hi) in self.handoff_buckets.items():
            if lo <= handoff_depth < hi:
                handoff_key = key
                break
        
        # Determine context bucket
        context_key = "0-30%"
        for key, (lo, hi) in self.context_buckets.items():
            if lo <= context_idle_pct < hi:
                context_key = key
                break
        
        regime_id = f"{tool_key}_{handoff_key}_{context_key}"
        
        return {
            "tool_bucket": tool_key,
            "handoff_bucket": handoff_key,
            "context_bucket": context_key,
            "regime_id": regime_id
        }
    
    def bucket_event(self, event_path: str, event_data: dict) -> dict:
        """
        将 event 分配到其 regime bucket.
        """
        tool_count = len(event_data.get("tools_used", []))
        handoff_depth = len(event_data.get("agent_chain", [])) - 1
        context_idle = event_data.get("context_idle_pct", 50)
        
        regime = self.compute_regime(tool_count, handoff_depth, context_idle)
        
        # Store event in regime-specific bucket
        bucket_path = self.tracking_dir / regime["regime_id"] / str(event_path).split("/")[-1]
        bucket_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Extract metrics for baseline calculation
        metrics = {
            k: v for k, v in event_data.items() 
            if k.startswith("metric_") or k in ["entity_loss_rate", "compression_event_count", "tool_latency"]
        }
        
        # Append to regime-specific timeseries
        timeseries_path = bucket_path.with_suffix(".jsonl")
        with open(timeseries_path, "a") as f:
            f.write(json.dumps({
                **metrics,
                "regime": regime,
                "timestamp": datetime.utcnow().isoformat()
            }) + "\n")
        
        return regime
    
    def get_regime_summary(self) -> dict:
        """
        返回当前各 regime 的样本计数和统计量.
        """
        summary = {}
        for bucket in self.tracking_dir.iterdir():
            if bucket.is_dir():
                regime_id = bucket.name
                stats = {"sample_count": 0, "metrics": {}}
                
                # Read from timeseries
                for timeseries in bucket.glob("*.jsonl"):
                    for line in timeseries.glob("*.jsonl"):
                        try:
                            with open(line) as f:
                                for _ in f:
                                    stats["sample_count"] += 1
                        except:
                            pass
                
                summary[regime_id] = stats
        
        return summary


def main():
    """
    监控脚本入口.
    """
    tracker = WorkloadComposer()
    
    # Example: process current session events
    # In production, would integrate with OpenClaw heartbeat loop
    print("Workload Composition Tracker initialized")
    print(f"Tracking directory: {tracker.tracking_dir}")
    print(f"Registered buckets: {list(tracker.tracking_dir.iterdir())}")


if __name__ == "__main__":
    main()
