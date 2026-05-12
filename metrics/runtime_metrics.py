#!/usr/bin/env python3
"""
Runtime Metrics Collector for Pentagon System
Collects continuous telemetry for governance and long-horizon monitoring.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import psutil

METRICS_PATH = Path(__file__).parent.parent / "metrics" / "runtime_metrics.jsonl"
METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)

def get_gpu_metrics():
    """Extract GPU metrics from nvidia-smi (or Ollama if available)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.memory,utilization.gpu,memory.total,memory.used,vram.total,vram.used",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split(",")
            if len(parts) >= 6:
                return {
                    "gpu_utilization": float(parts[1]),
                    "vram_used": float(parts[5]),
                    "vram_total": float(parts[4]),
                    "memory_used": float(parts[2]),
                    "memory_total": float(parts[3]),
                }
    except Exception:
        pass
    return {
        "gpu_utilization": 0.0,
        "vram_used": 0.0,
        "vram_total": 12.0,
        "memory_used": 0.0,
        "memory_total": 12.0,
    }

def get_event_loop_stats():
    """Estimate event loop pressure from process metrics."""
    proc = psutil.Process()
    try:
        threads = len(proc.threads())
        mem_percent = proc.memory_percent()
        cpu_percent = proc.cpu_percent()
        # Heuristic: infer pressure from thread count and memory
        event_loop_p99 = min(threads * 5 + mem_percent * 2, 300)  # ms
        return {
            "event_loop_p99": round(event_loop_p99, 2),
            "thread_count": threads,
            "memory_percent": round(mem_percent, 2),
            "cpu_percent": round(cpu_percent, 2),
        }
    except Exception:
        return {
            "event_loop_p99": 0.0,
            "thread_count": 0,
            "memory_percent": 0.0,
            "cpu_percent": 0.0,
        }

def get_queue_depth():
    """Estimate queue depth from openclaw task count."""
    try:
        result = subprocess.run(
            ["bash", "-c", "openclaw tasks 2>/dev/null | wc -l || echo 0"],
            capture_output=True, text=True, timeout=5
        )
        count = int(result.stdout.strip())
        return min(count, 20)
    except Exception:
        return 0

def get_context_usage():
    """Estimate context usage from episodic/semantic entry counts."""
    episodic = Path(__file__).parent.parent / "episodic.jsonl"
    semantic = Path(__file__).parent.parent / "semantic.jsonl"
    
    try:
        ep_count = sum(1 for _ in episodic.open())
        sem_count = sum(1 for _ in semantic.open())
        total = ep_count + sem_count
        return {
            "episodic_entries": ep_count,
            "semantic_entries": sem_count,
            "total_entries": total,
            "context_usage_percent": round((total / 5000) * 100, 2) if total < 5000 else 100.0,
        }
    except Exception:
        return {
            "episodic_entries": 0,
            "semantic_entries": 0,
            "total_entries": 0,
            "context_usage_percent": 0.0,
        }

def get_active_agents():
    """Count active subagent sessions."""
    try:
        result = subprocess.run(
            ["bash", "-c", "openclaw sessions list 2>/dev/null | grep -c 'active' || echo 0"],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except Exception:
        return 0

def get_tool_output_growth():
    """Estimate tool output growth from file stats."""
    try:
        workspace = Path(__file__).parent.parent
        for f in ["episodic.jsonl", "semantic.jsonl", "agents/*.jsonl"]:
            fp = workspace / f
            if fp.exists():
                stat = fp.stat()
                return {
                    "tool_output_bytes": stat.st_size,
                    "tool_output_lines": sum(1 for _ in fp.open()),
                }
    except Exception:
        pass
    return {"tool_output_bytes": 0, "tool_output_lines": 0}

def get_retrieval_metrics():
    """Estimate retrieval quality from qdrant latency (if available)."""
    # Placeholder for now
    return {
        "retrieval_rate": 0.0,
        "retrieval_latency_avg": 0.0,
        "retrieval_accuracy_estimate": 100.0,
    }

def get_compression_metrics():
    """Compression system health."""
    episodic = Path(__file__).parent.parent / "episodic.jsonl"
    try:
        with open(episodic) as f:
            lines = f.readlines()
        return {
            "total_lines": len(lines),
            "compression_threshold": 3000,
            "compression_ready": len(lines) >= 3000,
        }
    except Exception:
        return {
            "total_lines": 0,
            "compression_threshold": 3000,
            "compression_ready": False,
        }

def collect_all_metrics():
    """Collect all metrics and return as dict."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **get_event_loop_stats(),
        **get_queue_depth(),
        **get_context_usage(),
        **get_gpu_metrics(),
        **get_active_agents(),
        **get_tool_output_growth(),
        **get_retrieval_metrics(),
        **get_compression_metrics(),
    }

def write_metric(metrics):
    """Write metrics to JSONL file."""
    with open(METRICS_PATH, "a") as f:
        f.write(json.dumps(metrics) + "\n")

def main():
    """Main collection loop."""
    while True:
        metrics = collect_all_metrics()
        write_metric(metrics)
        print(json.dumps(metrics, indent=2))
        time.sleep(5)  # Collect every 5 seconds

if __name__ == "__main__":
    main()
