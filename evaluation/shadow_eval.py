#!/usr/bin/env python3
"""
Context Admission Control Experiment System
Shadow Mode: Non-invasive runtime observation

Variables:
- RPR (Retrieval Pollution Ratio)
- token_usage (per-turn)
- reset_perception (context reset events)

Constraints:
- NO runtime interference
- NO persistence beyond samples list
- NO CI coupling
- NO adaptive tuning
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os


class ShadowEvaluator:
    """Shadow runtime observer - no control authority."""

    def __init__(self, samples_dir: str = "evaluation/samples"):
        """Initialize shadow evaluator."""
        self.samples_dir = samples_dir
        self.metrics: List[Dict[str, Any]] = []
        self.config = {
            "interval_seconds": 3600,  # 1h reporting
            "metrics": ["rpr", "tokens", "resets"],
            "shadow_mode": True,  # CRITICAL: never False
        }
        os.makedirs(samples_dir, exist_ok=True)

    def observe_turn(self, rpr: float, token_usage: int, reset_perception: int) -> Dict[str, Any]:
        """
        Observe a single turn.
        Shadow mode: record metrics only, no runtime influence.
        """
        timestamp = datetime.now().isoformat()
        sample = {
            "timestamp": timestamp,
            "rpr": rpr,
            "tokens": token_usage,
            "resets": reset_perception,
            "config_snapshot": self.config.copy(),
        }
        self.metrics.append(sample)
        return sample

    def flush_metrics(self) -> List[Dict[str, Any]]:
        """Flush metrics to samples directory."""
        if not self.metrics:
            return []
        for i, sample in enumerate(self.metrics, start=1):
            path = os.path.join(self.samples_dir, f"{sample['timestamp'].replace(':', '-')}.json")
            with open(path, "w") as f:
                json.dump(sample, f, indent=2)
        count = len(self.metrics)
        self.metrics.clear()
        return self.metrics[:count]

    def report(self) -> Dict[str, Any]:
        """Generate 1h report (summary only)."""
        if not self.metrics:
            return {
                "status": "idle",
                "count": 0,
                "message": "No metrics collected yet.",
            }
        total_rpr = sum(s["rpr"] for s in self.metrics)
        total_tokens = sum(s["tokens"] for s in self.metrics)
        total_resets = sum(s["resets"] for s in self.metrics)
        avg_rpr = total_rpr / len(self.metrics)
        avg_tokens = total_tokens / len(self.metrics)
        avg_resets = total_resets / len(self.metrics)
        return {
            "status": "complete",
            "count": len(self.metrics),
            "summary": {
                "avg_rpr": avg_rpr,
                "avg_tokens": avg_tokens,
                "avg_resets": avg_resets,
            },
        }


def main():
    """Shadow runtime observer."""
    evaluator = ShadowEvaluator()
    print(f"[{datetime.now().isoformat()}] Shadow evaluator initialized.")
    print(f"  → Mode: shadow only (no runtime interference)")
    print(f"  → Report interval: {evaluator.config['interval_seconds']}s")
    # In actual deployment, hook into runtime loop:
    #   for turn in runtime_stream:
    #       sample = evaluator.observe_turn(...)
    #       evaluator.flush_metrics()
    # For now, demo with dummy data:
    print("[Demo] Observing 10 turns with dummy metrics...")
    for i in range(10):
        sample = evaluator.observe_turn(
            rpr=0.05 + i * 0.005,
            token_usage=4096 - i * 100,
            reset_perception=0 if i > 2 else 1,
        )
        print(f"  → Turn {i}: RPR={sample['rpr']:.3f}, tokens={sample['tokens']}")
    report = evaluator.report()
    print(f"\n[Report] {report['count']} samples collected.")
    if report['status'] == 'complete':
        print(f"  → Avg RPR: {report['summary']['avg_rpr']:.3f}")
        print(f"  → Avg tokens: {report['summary']['avg_tokens']:.0f}")
        print(f"  → Avg resets: {report['summary']['avg_resets']:.3f}")


if __name__ == "__main__":
    main()
