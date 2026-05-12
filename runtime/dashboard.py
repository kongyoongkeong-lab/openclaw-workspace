#!/usr/bin/env python3
"""
Pentagon Real-Time Metrics Dashboard
Generates latency graphs, cache ratios, token usage, and degradation reports.
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path

# Configuration
WORKSPACE = "/home/jason2ykk/.openclaw/workspace"
RUNTIME_DIR = os.path.join(WORKSPACE, "runtime")
LOGS_DIR = os.path.join(WORKSPACE, "runtime_logs")
MEMORY_DIR = os.path.join(WORKSPACE, "memory")
OUTPUT_DIR = os.path.join(WORKSPACE, "runtime/dashboard_output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_telemetry(agent):
    """Read telemetry data from agent logs."""
    log_path = os.path.join(LOGS_DIR, f"{agent}.log")
    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            lines = f.readlines()
            return [line.strip() for line in lines if line.strip() and agent in line]
    return []

def analyze_agent_health(agents):
    """Analyze health metrics for all agents."""
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "agents": {},
        "summary": {
            "total_tokens": 0,
            "cache_hits": 0,
            "hallucinations": 0,
            "truncations": 0,
            "degradation_events": 0
        }
    }
    
    for agent_id in agents:
        agent_logs = read_telemetry(agent_id)
        
        # Calculate token usage from logs
        tokens_used = sum(
            int(line.split(" tokens")[1].split("]")[0]) 
            for line in agent_logs 
            if "tokens" in line
        )
        
        # Check for cache events
        cache_hits = sum(
            1 for line in agent_logs if "cache" in line.lower() and "hit" in line.lower()
        )
        cache_misses = sum(
            1 for line in agent_logs if "cache" in line.lower() and "miss" in line.lower()
        )
        
        # Check for hallucinations
        hallucinations = sum(
            1 for line in agent_logs if "hallucination" in line.lower() or "fabricated" in line.lower()
        )
        
        # Check for truncations
        truncations = sum(
            1 for line in agent_logs if "truncate" in line.lower() or "token_limit" in line.lower()
        )
        
        # Check for degradation
        degradation = sum(
            1 for line in agent_logs if "degradation" in line.lower() or "failure" in line.lower()
        )
        
        metrics["agents"][agent_id] = {
            "tokens_used": tokens_used,
            "cache_hit_ratio": cache_hits / (cache_hits + cache_misses) if (cache_hits + cache_misses) > 0 else 0,
            "hallucinations": hallucinations,
            "truncations": truncations,
            "degradation_events": degradation,
            "status": "healthy" if hallucinations == 0 and truncations == 0 else "degraded"
        }
        
        metrics["summary"]["total_tokens"] += tokens_used
        metrics["summary"]["cache_hits"] += cache_hits
        metrics["summary"]["hallucinations"] += hallucinations
        metrics["summary"]["truncations"] += truncations
        metrics["summary"]["degradation_events"] += degradation
    
    return metrics

def generate_latency_graph(agent_logs):
    """Generate a simple text-based latency graph."""
    latencies = []
    for line in agent_logs:
        if "latency" in line.lower() and ":ms" in line:
            try:
                val = line.split(":")[1].strip().split("ms")[0]
                latencies.append(int(float(val)))
            except:
                pass
    
    if not latencies:
        return "No latency data available"
    
    # Create histogram
    max_lat = max(latencies)
    bins = []
    for i in range(0, max_lat + 1, 5):
        count = sum(1 for lat in latencies if i <= lat < i + 5)
        bars = "█" * min(count, 10)  # Cap bars at 10 for readability
        bins.append(f"{i}-{min(i+5-1, max_lat)}: {bars} ({count})")
    
    return "\n".join(bins)

def generate_degradation_report(metrics):
    """Generate structured degradation report."""
    report = []
    report.append(f"## Degradation Report ({metrics['timestamp']})")
    report.append("")
    report.append(f"### Summary")
    report.append(f"- **Total Tokens**: {metrics['summary']['total_tokens']}")
    report.append(f"- **Cache Hits**: {metrics['summary']['cache_hits']}")
    report.append(f"- **Hallucinations**: {metrics['summary']['hallucinations']}")
    report.append(f"- **Truncations**: {metrics['summary']['truncations']}")
    report.append(f"- **Degradation Events**: {metrics['summary']['degradation_events']}")
    report.append("")
    report.append("### Agent Health")
    
    for agent_id, agent_data in metrics['agents'].items():
        status_icon = "✅" if agent_data['status'] == 'healthy' else "⚠️"
        report.append(f"- **{agent_id}** {status_icon}")
        report.append(f"  - Tokens: {agent_data['tokens_used']}")
        report.append(f"  - Cache Hit Ratio: {agent_data['cache_hit_ratio']:.1%}")
        report.append(f"  - Hallucinations: {agent_data['hallucinations']}")
        report.append(f"  - Truncations: {agent_data['truncations']}")
        report.append(f"  - Status: {agent_data['status']}")
        report.append("")
    
    if metrics['summary']['hallucinations'] > 0 or metrics['summary']['degradation_events'] > 0:
        report.append("### ⚠️ ALERT: Degradation Detected")
        report.append(f"- Hallucination Count: {metrics['summary']['hallucinations']}")
        report.append(f"- Degradation Events: {metrics['summary']['degradation_events']}")
        report.append("- Immediate intervention recommended")
    
    return "\n".join(report)

def main():
    """Main monitoring loop."""
    print("=" * 60)
    print("PENTAGON REAL-TIME METRICS DASHBOARD")
    print("=" * 60)
    print("")
    
    agents = ["intel", "ops", "comms", "sentinel"]
    metrics = analyze_agent_health(agents)
    
    print(generate_degradation_report(metrics))
    print("")
    print("### Token Usage by Agent")
    for agent_id, data in metrics['agents'].items():
        print(f"- {agent_id}: {data['tokens_used']} tokens")
    
    print("")
    print("### Cache Hit Ratios")
    for agent_id, data in metrics['agents'].items():
        print(f"- {agent_id}: {data['cache_hit_ratio']:.1%}")
    
    print("")
    
    # Save metrics to file
    output_file = os.path.join(OUTPUT_DIR, f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    with open(output_file, 'w') as f:
        f.write(generate_degradation_report(metrics))
    
    print(f"Metrics saved to: {output_file}")
    
    # Check if any agent is degraded
    if metrics['summary']['hallucinations'] > 0 or metrics['summary']['degradation_events'] > 0:
        print("")
        print("🚨 DEGRADATION DETECTED - Taking corrective action...")
    
    return metrics

if __name__ == "__main__":
    main()
