#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24h Stability Dashboard Collector (Observability-only)
Three-axis: CI Stability | Runtime Health | Divergence Score
"""

import json
from datetime import datetime
from pathlib import Path


class StabilityCollector:
    """Minimal collector for CI/Runtime/Divergence metrics."""

    def __init__(self):
        self.ci_history = []
        self.runtime_history = []
        self.divergence_history = []
        self.events = []
        self.base_path = Path("/home/jason2ykk/.openclaw/workspace")
        self.output_dir = self.base_path / "stability"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def collect_ci(self) -> int:
        """Collect CI stability (pass/fail rolling ratio)."""
        # Replace with actual CI result check from logs
        ci_pass = 1
        self.ci_history.append(ci_pass)
        return ci_pass

    def collect_runtime(self) -> int:
        """Collect Runtime health status."""
        # Replace with actual runtime health check
        runtime_ok = 0
        self.runtime_history.append(runtime_ok)
        return runtime_ok

    def compute_divergence(self, ci: int, runtime: int) -> int:
        """Compute divergence score: abs(CI_result - runtime_result)."""
        divergence = abs(ci - runtime)
        self.divergence_history.append(divergence)
        return divergence

    def record_event(self, event: str):
        """Record diagnostic events."""
        self.events.append(event)
        print(f"⚠ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {event}")

    def get_metrics(self) -> dict:
        """Return current metrics snapshot."""
        ci = self.ci_history[-1] if self.ci_history else 0
        runtime = self.runtime_history[-1] if self.runtime_history else 0
        divergence = self.divergence_history[-1] if self.divergence_history else 0

        return {
            "timestamp": datetime.now().isoformat(),
            "ci": ci,
            "runtime": runtime,
            "divergence": divergence,
            "events": self.events,
            "ci_1h_ratio": self._rolling_ratio(self.ci_history, 1),
            "ci_6h_ratio": self._rolling_ratio(self.ci_history, 6),
            "ci_24h_ratio": self._rolling_ratio(self.ci_history, 24),
            "crash_count": len([r for r in self.runtime_history if r == 1]),
            "reconnect_count": 0,
            "event_loop_stalls": 0,
        }

    def _rolling_ratio(self, history: list, window: int) -> float:
        """Compute rolling pass/fail ratio."""
        if len(history) < window:
            return 1.0
        window_data = history[-window:]
        return sum(window_data) / len(window_data)

    def save_json(self):
        """Save JSON timeline snapshot."""
        metrics = self.get_metrics()
        file_path = self.output_dir / "stability.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        return file_path

    def save_cli(self):
        """Save CLI timeline view (debug)."""
        metrics = self.get_metrics()
        lines = []
        lines.append(f"t=00h CI={metrics['ci']} Runtime={metrics['runtime']} Divergence={metrics['divergence']}")
        lines.append(f"  CI_1h={metrics['ci_1h_ratio']:.2f} CI_6h={metrics['ci_6h_ratio']:.2f} CI_24h={metrics['ci_24h_ratio']:.2f}")
        lines.append(f"  CrashCount={metrics['crash_count']} ReconnectCount=0 Stalls=0")
        
        if metrics['divergence'] > 0:
            lines.append("⚠ Divergence detected")
        else:
            lines.append("✅ Stable")
        
        if metrics['events']:
            lines.append(f"  Events: {', '.join(metrics['events'])}")
        
        content = "\n".join(lines)
        file_path = self.output_dir / "stability_cli.txt"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return file_path

    def collect_snapshot(self) -> dict:
        """Full collection cycle."""
        ci = self.collect_ci()
        runtime = self.collect_runtime()
        divergence = self.compute_divergence(ci, runtime)
        return self.get_metrics()


def main():
    """Main entry point."""
    collector = StabilityCollector()

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting Stability Collector...")
    
    # Collect metrics
    metrics = collector.collect_snapshot()
    
    # Save outputs
    json_path = collector.save_json()
    cli_path = collector.save_cli()
    
    # Print CLI view
    with open(cli_path, "r", encoding="utf-8") as f:
        print(f"\n📊 CLI View:\n{f.read()}")
    
    # Save to workspace
    with open("/home/jason2ykk/.openclaw/workspace/stability_cli.txt", "w", encoding="utf-8") as f:
        f.write(f.read())
    
    print(f"✅ JSON: {json_path}")
    print(f"✅ CLI: {cli_path}")


if __name__ == "__main__":
    main()
