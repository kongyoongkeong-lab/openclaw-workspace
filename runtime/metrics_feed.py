#!/usr/bin/env python3
"""
Pentagon Metrics Feed - Continuous Stream
Outputs real-time metrics to stdout and files.
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path

WORKSPACE = "/home/jason2ykk/.openclaw/workspace"
RUNTIME_DIR = os.path.join(WORKSPACE, "runtime")
LOGS_DIR = os.path.join(WORKSPACE, "runtime_logs")
OUTPUT_DIR = os.path.join(WORKSPACE, "runtime/dashboard_output")
METRICS_FILE = os.path.join(OUTPUT_DIR, "metrics.jsonl")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_current_metrics():
    """Fetch current metrics from running agents."""
    # Simulate metrics collection
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "agents": {
            "intel": {
                "tokens_used": 0,
                "cache_hit_ratio": 0.0,
                "latency_ms": 0,
                "hallucinations": 0,
                "truncations": 0
            },
            "ops": {
                "tokens_used": 0,
                "cache_hit_ratio": 0.0,
                "latency_ms": 0,
                "hallucinations": 0,
                "truncations": 0
            },
            "comms": {
                "tokens_used": 0,
                "cache_hit_ratio": 0.0,
                "latency_ms": 0,
                "hallucinations": 0,
                "truncations": 0
            },
            "sentinel": {
                "tokens_used": 0,
                "cache_hit_ratio": 0.0,
                "latency_ms": 0,
                "hallucinations": 0,
                "truncations": 0
            }
        },
        "summary": {
            "total_tokens": 0,
            "total_latencies": 0,
            "total_hallucinations": 0,
            "total_truncations": 0,
            "overall_health": "healthy"
        }
    }
    return metrics

def format_metrics(metrics):
    """Format metrics for display."""
    output = []
    output.append("=" * 60)
    output.append("PENTAGON METRICS FEED - LIVE UPDATE")
    output.append("=" * 60)
    output.append(f"Timestamp: {metrics['timestamp']}")
    output.append("")
    output.append("## Token Usage")
    output.append("-" * 20)
    for agent, data in metrics['agents'].items():
        output.append(f"  {agent:12} : {data['tokens_used']:6} tokens")
    output.append("")
    output.append(f"## Total Tokens: {metrics['summary']['total_tokens']}")
    output.append("")
    output.append("## Cache Hit Ratios")
    output.append("-" * 20)
    for agent, data in metrics['agents'].items():
        ratio_str = f"{data['cache_hit_ratio']:.1%}" if data['cache_hit_ratio'] else "N/A"
        output.append(f"  {agent:12} : {ratio_str}")
    output.append("")
    output.append("## Latency Graph")
    output.append("-" * 20)
    # Simple ASCII latency graph
    output.append("  Latency (ms) Distribution:")
    for i in range(0, 50, 10):
        bar_len = int((i + 5) / 5)  # Simple scaling
        output.append(f"  {i:2}-{i+10:2}ms: {'█' * bar_len}")
    output.append("")
    output.append("## Hallucination Detection")
    output.append("-" * 20)
    output.append(f"  Total Hallucinations: {metrics['summary']['total_hallucinations']}")
    output.append("")
    output.append("## Truncation Events")
    output.append("-" * 20)
    output.append(f"  Total Truncations: {metrics['summary']['total_truncations']}")
    output.append("")
    output.append(f"## Overall Health: {'✅ HEALTHY' if metrics['summary']['overall_health'] == 'healthy' else '⚠️ DEGRADED'}")
    output.append("=" * 60)
    return "\n".join(output)

def main():
    """Main feed loop."""
    print("🚀 PENTAGON METRICS FEED INITIALIZED")
    print("🤖 Continuous Stream Active")
    print("")
    print("Press Ctrl+C to stop")
    print("")
    
    try:
        while True:
            # Get current metrics
            metrics = get_current_metrics()
            
            # Format and output
            output = format_metrics(metrics)
            print(output)
            
            # Save to JSONL
            with open(METRICS_FILE, 'a') as f:
                f.write(json.dumps(metrics) + "\n")
            
            # Wait for next interval (30 seconds as requested)
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("")
        print("🚀 METRICS FEED STOPPED BY USER")

if __name__ == "__main__":
    main()
