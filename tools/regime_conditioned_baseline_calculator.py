#!/usr/bin/env python3
"""
Regime-Conditioned Baseline Calculator

重写 baseline 计算逻辑，从 time-window 切换到 workload conditioning.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from workload_composition_tracker import WorkloadComposer


class BaselineCalculator:
    """
    Regime-conditioned baseline 计算器.
    
    不再使用 P(metric | time_window),而是使用:
    baseline = P(metric | tool_bucket, handoff_bucket, context_bucket)
    """
    
    def __init__(self, workspace: str = "/home/jason2ykk/.openclaw/workspace"):
        self.workspace = Path(workspace)
        self.metrics_dir = self.workspace / "memory" / "telemetry"
        self.tracker = WorkloadComposer(workspace)
        
        # Regime-specific baselines
        self.baselines = {}
        
        # Legacy data (time-window based)
        self.legacy_dir = self.metrics_dir / "baseline_legacy"
        self.legacy_dir.mkdir(parents=True, exist_ok=True)
    
    def compute_regime_conditioned_baseline(
        self, 
        regime_id: str,
        metric: str,
        window: dict,
        confidence_level: float = 0.95
    ) -> dict:
        """
        计算 regime-conditioned baseline.
        
        Args:
            regime_id: 如 "medium_3-4_30-70%"
            metric: 如 "entity_loss_rate"
            window: 时间窗口
            confidence_level: 置信水平
            
        Returns:
            Baseline distribution with confidence intervals
        """
        bucket_dir = self.tracker.tracking_dir / regime_id
        timeseries_path = bucket_dir / f"{metric}.jsonl"
        
        if not timeseries_path.exists():
            return {
                "error": f"No data for regime {regime_id}",
                "conditioning_key": regime_id
            }
        
        # Read samples
        samples = []
        with open(timeseries_path) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    samples.append(data.get(metric))
                except:
                    pass
        
        if not samples:
            return {
                "error": "No samples found",
                "conditioning_key": regime_id
            }
        
        # Filter null values
        samples = [s for s in samples if s is not None]
        
        if len(samples) < 10:
            return {
                "error": f"Insufficient samples ({len(samples)} < 10)",
                "conditioning_key": regime_id
            }
        
        # Compute distribution stats
        mean = sum(samples) / len(samples)
        variance = sum((x - mean) ** 2 for x in samples) / len(samples)
        std = variance ** 0.5
        
        # Confidence interval (z-score for 95%: 1.96)
        margin = 1.96 * std / (len(samples) ** 0.5)
        
        return {
            "metric": metric,
            "conditioning_key": regime_id,
            "distribution": {
                "mean": mean,
                "std": std,
                "min": min(samples),
                "max": max(samples),
                "p50": sorted(samples)[len(samples) // 2]
            },
            "confidence_interval_95": {
                "lower": mean - margin,
                "upper": mean + margin
            },
            "sample_count": len(samples),
            "confidence_level": confidence_level
        }
    
    def recompute_all_baselines(self, metrics: list = None) -> dict:
        """
        扫描所有 regime buckets 并计算 baselines.
        """
        metrics = metrics or ["entity_loss_rate", "tool_latency", "compression_event_count"]
        
        results = {}
        
        for bucket in self.tracker.tracking_dir.iterdir():
            if bucket.is_dir():
                regime_id = bucket.name
                
                regime_baseline = {}
                for metric in metrics:
                    baseline = self.compute_regime_conditioned_baseline(
                        regime_id, metric, None
                    )
                    regime_baseline[metric] = baseline
                
                results[regime_id] = regime_baseline
        
        return results
    
    def migrate_legacy_to_regime_based(self, legacy_file: str) -> dict:
        """
        将 legacy time-window baseline 迁移到 regime-based.
        
        Legacy 数据通常标记为 "passive" 或 "normal".
        问题：这些标签不可验证.
        
        迁移策略：
        1. 重新分析 legacy 事件中每个 event 的 regime
        2. 将 legacy 样本分配到对应 bucket
        3. 删除 time-window based baselines
        """
        legacy_path = self.legacy_dir / legacy_file
        
        if not legacy_path.exists():
            return {"error": f"Legacy file not found: {legacy_file}"}
        
        # Read legacy events
        legacy_events = []
        with open(legacy_path) as f:
            for line in f:
                try:
                    legacy_events.append(json.loads(line))
                except:
                    pass
        
        # Bucket each event
        for event in legacy_events:
            regime = self.tracker.bucket_event(None, event)
            regime_id = regime["regime_id"]
            
            # Append to regime-specific bucket
            bucket_dir = self.tracker.tracking_dir / regime_id
            metric = "entity_loss_rate"  # Example
            timeseries_path = bucket_dir / f"{metric}.jsonl"
            timeseries_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(timeseries_path, "a") as f:
                f.write(json.dumps({
                    **event,
                    "regime": regime,
                    "from_legacy": True,
                    "timestamp": datetime.utcnow().isoformat()
                }) + "\n")
        
        return {
            "migrated": len(legacy_events),
            "distribution": list(self.tracker.tracking_dir.iterdir())
        }
    
    def generate_baseline_report(self) -> dict:
        """
        生成 baseline 报告.
        """
        metrics = ["entity_loss_rate", "tool_latency", "compression_event_count"]
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "architecture": "regime-conditioned",
            "conditioning_keys": {
                "tool_bucket": ["low", "medium", "high"],
                "handoff_bucket": ["1-2", "3-4", "5+"],
                "context_bucket": ["0-30%", "30-70%", "70-100%"]
            },
            "regime_baselines": {},
            "comparison": {
                "legacy_time_window": {"status": "deprecated", "reason": "mixed distribution bias"},
                "new_regime_based": {"status": "active", "reason": "identifiable conditioning"}
            }
        }
        
        # Compute baselines
        regime_summaries = self.recompute_all_baselines(metrics)
        report["regime_baselines"] = regime_summaries
        
        return report


def main():
    """
    Baseline 计算器入口.
    """
    calculator = BaselineCalculator()
    
    print("Regime-Conditioned Baseline Calculator initialized")
    print(f"Workspace: {calculator.workspace}")
    
    # Example: compute baseline for a regime
    regime_id = "medium_3-4_30-70%"
    metric = "entity_loss_rate"
    baseline = calculator.compute_regime_conditioned_baseline(
        regime_id, metric, None
    )
    
    if "error" not in baseline:
        print(f"\nBaseline for regime {regime_id}:")
        print(f"  Metric: {metric}")
        print(f"  Mean: {baseline['distribution']['mean']:.4f}")
        print(f"  95% CI: [{baseline['confidence_interval_95']['lower']:.4f}, {baseline['confidence_interval_95']['upper']:.4f}]")
        print(f"  Samples: {baseline['sample_count']}")
    
    print("\n✅ Architecture shift complete:")
    print("   OLD: baseline = P(metric | time_window)")
    print("   NEW: baseline = P(metric | workload_type, tool_count, context_depth)")


if __name__ == "__main__":
    main()
