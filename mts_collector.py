#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MTS Collector (Minimal Truth Sources)
Three-input truth sensor for Reality Alignment
"""

import json
from datetime import datetime
from pathlib import Path


class MTSCollector:
    """Minimal Truth Sources: CI + Runtime + Divergence."""

    def __init__(self):
        self.base_path = Path("/home/jason2ykk/.openclaw/workspace")
        self.output_dir = self.base_path / "stability"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Signal sources (placeholders for now)
        self.ci_source_path = self.base_path / "ci_status.json"
        self.runtime_source_path = self.base_path / "runtime_status.json"
        
        # Default values (will be replaced by real sources)
        self.ci_default = 1
        self.runtime_default = 1
        
        # Divergence
        self.divergence = 0
        self.events = []

    def get_ci_status(self) -> int:
        """Get CI status from GitHub Actions / pytest exit code."""
        # Try to read CI status from source
        try:
            if self.ci_source_path.exists():
                ci_data = json.loads(self.ci_source_path.read_text())
                return ci_data.get("status", 1)
        except:
            pass
        
        # Fallback: assume stable
        self.record_event("CI status unknown (assuming OK)")
        return self.ci_default

    def get_runtime_status(self) -> int:
        """Get Runtime status from Discord bot heartbeat."""
        try:
            if self.runtime_source_path.exists():
                runtime_data = json.loads(self.runtime_source_path.read_text())
                return runtime_data.get("alive", 1)
        except:
            pass
        
        # Fallback: assume stable
        self.record_event("Runtime status unknown (assuming OK)")
        return self.runtime_default

    def compute_divergence(self, ci: int, runtime: int) -> int:
        """Compute divergence: ci != runtime → 1, else 0."""
        divergence = abs(ci - runtime)
        self.divergence = divergence
        if divergence > 0:
            self.record_event(f"Divergence: CI={ci}, Runtime={runtime}, Score={divergence}")
        return divergence

    def record_event(self, event: str):
        """Record diagnostic events."""
        self.events.append(event)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠ {event}")

    def collect(self) -> dict:
        """Collect all three signals and compute divergence."""
        ci = self.get_ci_status()
        runtime = self.get_runtime_status()
        divergence = self.compute_divergence(ci, runtime)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ci": ci,
            "runtime": runtime,
            "divergence": divergence,
            "events": self.events,
            "ci_1h_ratio": 1.0,  # Placeholder
            "ci_6h_ratio": 1.0,  # Placeholder
            "ci_24h_ratio": 1.0, # Placeholder
            "crash_count": 0,
            "reconnect_count": 0,
            "event_loop_stalls": 0,
        }

    def save(self):
        """Save snapshots to output_dir and workspace root."""
        metrics = self.collect()
        
        # Save to stability directory
        with open(self.output_dir / "stability.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        # Save to workspace root
        with open(self.base_path / "stability.json", "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
        
        # Save CLI view
        lines = []
        lines.append(f"t={datetime.now().strftime('%H:%M')}:00h CI={metrics['ci']} Runtime={metrics['runtime']} Divergence={metrics['divergence']}")
        lines.append(f"  CI_1h={metrics['ci_1h_ratio']:.2f} CI_6h={metrics['ci_6h_ratio']:.2f} CI_24h={metrics['ci_24h_ratio']:.2f}")
        lines.append(f"  CrashCount={metrics['crash_count']} ReconnectCount=0 Stalls=0")
        if metrics['divergence'] == 0:
            lines.append("✅ Stable")
        else:
            lines.append(f"⚠ Divergence detected (score: {metrics['divergence']})")
        if metrics['events']:
            lines.append(f"  Events: {', '.join(metrics['events'])}")
        
        with open(self.base_path / "stability_cli.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"\n📊 MTS Metrics:")
        print(f"  CI: {metrics['ci']} | Runtime: {metrics['runtime']} | Divergence: {metrics['divergence']}")
        print(f"  CI_1h: {metrics['ci_1h_ratio']:.2f} | CI_6h: {metrics['ci_6h_ratio']:.2f} | CI_24h: {metrics['ci_24h_ratio']:.2f}")
        print(f"  CrashCount: {metrics['crash_count']}")
        print(f"\n✅ JSON: stability/stability.json")
        print(f"✅ CLI: stability_cli.txt")
        
        return metrics


def main():
    """Run MTS collector."""
    collector = MTSCollector()
    return collector.save()


if __name__ == "__main__":
    main()
