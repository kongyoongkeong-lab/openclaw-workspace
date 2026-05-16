#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
24h Stability Dashboard Collector - Initial Snapshot Generator
"""

import json
from datetime import datetime
from pathlib import Path


def generate_initial_snapshot():
    """Generate initial 24h Stability Dashboard snapshot."""
    base_path = Path("/home/jason2ykk/.openclaw/workspace")
    output_dir = base_path / "stability"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initial metrics (will be updated by periodic runs)
    timestamp = datetime.now().isoformat()
    ci = 1  # Initial: assume OK
    runtime = 1  # Initial: assume OK
    divergence = abs(ci - runtime)
    
    metrics = {
        "timestamp": timestamp,
        "ci": ci,
        "runtime": runtime,
        "divergence": divergence,
        "events": [],
        "ci_1h_ratio": 1.0,
        "ci_6h_ratio": 1.0,
        "ci_24h_ratio": 1.0,
        "crash_count": 0,
        "reconnect_count": 0,
        "event_loop_stalls": 0,
    }
    
    # Save JSON snapshot
    json_path = output_dir / "stability.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON: {json_path}")
    
    # Save CLI view
    cli_path = output_dir / "stability_cli.txt"
    lines = []
    lines.append(f"t=00h CI={metrics['ci']} Runtime={metrics['runtime']} Divergence={metrics['divergence']}")
    lines.append(f"  CI_1h={metrics['ci_1h_ratio']:.2f} CI_6h={metrics['ci_6h_ratio']:.2f} CI_24h={metrics['ci_24h_ratio']:.2f}")
    lines.append(f"  CrashCount={metrics['crash_count']} ReconnectCount=0 Stalls=0")
    if metrics['divergence'] == 0:
        lines.append("✅ Stable")
    else:
        lines.append("⚠ Divergence detected")
    content = "\n".join(lines)
    with open(cli_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ CLI: {cli_path}")
    
    # Copy to workspace root
    with open(json_path, "r", encoding="utf-8") as src:
        json_content = src.read()
    with open(base_path / "stability_initial.json", "w", encoding="utf-8") as dst:
        dst.write(json_content)
    print(f"✅ Copied: stability_initial.json")
    
    with open(cli_path, "r", encoding="utf-8") as src:
        cli_content = src.read()
    with open(base_path / "stability_initial_cli.txt", "w", encoding="utf-8") as dst:
        dst.write(cli_content)
    print(f"✅ Copied: stability_initial_cli.txt")
    
    return metrics


if __name__ == "__main__":
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Generating Initial Snapshot...")
    metrics = generate_initial_snapshot()
    print(f"✅ Snapshot generated successfully!")
    print(f"\n📊 Initial State:")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
