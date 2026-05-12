# @main Orchestrator with CEG Integration
"""
Central orchestrator with Governance Overhead % (GO%) tracking.
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional

# Import CEG modules
sys.path.insert(0, str(Path(__file__).parent))
from telemetry_integration import (
    compute_go_percent,
    run_all_ceg_metrics
)
from idle_context_occupancy import run_idle_context_analysis, IDLE_THRESHOLD_CRITICAL

# Configuration
MAIN_AGENT = "@main"
GO_PERCENT_THRESHOLD_CRITICAL = 35
GO_PERCENT_THRESHOLD_HEAVY = 20
IDLE_THRESHOLD_CRITICAL = 50

def orchestrate_inference_cycle(
    agent_outputs: List[Dict],
    retrieved_ids: List[str],
    reasoning_referenced_ids: List[str],
    governance_tokens: int = 500,
    productive_tokens: int = 4500
) -> Dict:
    """Orchestrate inference cycle with CEG metrics."""
    
    # Compute metrics
    metrics = run_all_ceg_metrics({
        "retrieved_ids": retrieved_ids,
        "reasoning_referenced_ids": reasoning_referenced_ids,
        "governance_tokens": governance_tokens,
        "productive_tokens": productive_tokens
    })
    
    # Run idle context analysis
    idle_report = run_idle_context_analysis(current_turn=10)
    
    # Create orchestration summary
    summary = {
        "ceg_metrics": {
            "rur": {
                "value": metrics["rur"]["rur"],
                "ratio": metrics["rur"]["ratio"]
            },
            "go_percent": {
                "value": metrics["go_percent"]["go_percent"],
                "ratio": metrics["go_percent"]["ratio"]
            }
        },
        "idle_context": {
            "idle_percent": idle_report.idle_percent,
            "total_slots": idle_report.total_slots,
            "idle_slots": idle_report.idle_slots
        }
    }
    
    # Evaluate and recommend
    recommendations = []
    
    # Evaluate RUR
    if metrics["rur"]["ratio"] == "CRITICAL":
        recommendations.append("🚨 CRITICAL: Request more targeted search from @intel")
    elif metrics["rur"]["ratio"] == "WARNING":
        recommendations.append("🔍 WARNING: Refine search query for higher RUR")
    
    # Evaluate GO%
    if metrics["go_percent"]["ratio"] == "COLLAPSE":
        recommendations.append("🚨 COLLAPSE: Optimize token usage, reduce governance overhead")
    elif metrics["go_percent"]["ratio"] == "HEAVY":
        recommendations.append("⚠️ HEAVY: Consider offloading to cloud API")
    
    # Evaluate idle context
    if idle_report.idle_percent >= IDLE_THRESHOLD_CRITICAL:
        recommendations.append("🚨 CRITICAL: Evict idle context slots (>50%)")
    elif idle_report.idle_percent >= 30:
        recommendations.append("⚠️ WARNING: Compress idle context (>30%)")
    
    summary["recommendations"] = recommendations
    summary["action_required"] = len(recommendations) > 0
    
    return summary

def delegate_to_agents(
    task: str,
    agents: List[str] = None
) -> Dict:
    """Delegate task to agents with CEG tracking."""
    
    if agents is None:
        agents = ["@intel", "@ops", "@comms", "@sentinel"]
    
    # Create task payload
    task_payload = {
        "task": task,
        "agents": agents,
        "ceg_tracking": True
    }
    
    return task_payload

if __name__ == "__main__":
    # Demo
    demo_outputs = [
        {"retrieved_ids": ["r1", "r2", "r3", "r4", "r5"], "referenced_ids": ["r1", "r3"]},
        {"retrieved_ids": ["r6", "r7"], "referenced_ids": ["r6"]}
    ]
    
    result = orchestrate_inference_cycle(
        agent_outputs=demo_outputs,
        retrieved_ids=["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
        reasoning_referenced_ids=["r1", "r3", "r6"],
        governance_tokens=500,
        productive_tokens=4500
    )
    
    print("CEG Metrics Summary:")
    print(f"  RUR: {result['ceg_metrics']['rur']['value']:.4f} ({result['ceg_metrics']['rur']['ratio']})")
    print(f"  GO%: {result['ceg_metrics']['go_percent']['value']:.2f}% ({result['ceg_metrics']['go_percent']['ratio']})")
    print(f"  Idle Context: {result['idle_context']['idle_percent']:.1f}%")
    print(f"  Recommendations: {len(result['recommendations'])}")
    for rec in result["recommendations"]:
        print(f"    - {rec}")
