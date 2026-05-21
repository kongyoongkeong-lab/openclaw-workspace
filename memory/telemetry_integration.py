# Telemetry Integration Layer
"""
Integrate CEG metrics into Pentagon Agent workflow.

Integration Points:
1. @intel: After retrieval batch → compute RUR
2. @main: After inference cycle → compute GO%
3. @ops: Periodically → run Idle Context Analysis
4. All agents: Log to telemetry tiering system
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timezone

MEMORY_DIR = Path(__file__).parent / "memory"
EPISODIC_FILE = MEMORY_DIR / "episodic.jsonl"
SEMANTIC_FILE = MEMORY_DIR / "semantic.jsonl"
COMPRESSION_FILE = MEMORY_DIR / "compression.jsonl"

# Telemetry tiering configuration
TELEMETRY_TIERS = {
    "HOT": {
        "retention_minutes": 5,
        "storage": "memory",
        "cleanup": "soft_eviction"
    },
    "WARM": {
        "retention_hours": 24,
        "storage": "aggregated_summary",
        "cleanup": "daily_rollup"
    },
    "COLD": {
        "retention_days": 7,
        "storage": "statistics_only",
        "cleanup": "weekly_archive"
    },
    "DEAD": {
        "retention_days": 0,
        "storage": "deleted",
        "cleanup": "immediate"
    }
}


def tier_telemetry(telemetry_type: str, timestamp: float) -> str:
    """Determine tier for telemetry data."""
    if telemetry_type in ["retrieval", "compression", "repair"]:
        if timestamp > datetime.now(timezone.utc).timestamp() - 5*60:
            return "HOT"
        elif timestamp > datetime.now(timezone.utc).timestamp() - 24*60*60:
            return "WARM"
        elif timestamp > datetime.now(timezone.utc).timestamp() - 7*24*60*60:
            return "COLD"
        else:
            return "DEAD"
    return "HOT"


def log_ceg_metrics(metrics: Dict, event_type: str) -> Optional[Dict]:
    """Log Cognitive Efficiency Governance metrics to episodic memory."""
    
    # Tier the telemetry
    tier = tier_telemetry(event_type, datetime.now(timezone.utc).timestamp())
    
    # Create entry
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tier": tier,
        "type": event_type,
        "category": "ceg_metrics",
        "data": metrics
    }
    
    # Append to episodic memory
    with open(EPISODIC_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    return entry


def compute_rur(retrieved_ids: List[str], reasoning_reference_ids: List[str]) -> Dict:
    """Compute Retrieval Usefulness Ratio."""
    retrieved_set = set(retrieved_ids)
    referenced_set = set(reasoning_reference_ids)
    
    intersection = retrieved_set & referenced_set
    useful_count = len(intersection)
    total_retrieved = len(retrieved_ids)
    
    rur = useful_count / total_retrieved if total_retrieved > 0 else 0.0
    
    return {
        "rur": round(rur, 4),
        "productive_retrievals": useful_count,
        "total_retrievals": total_retrieved,
        "ratio": "EXCELLENT" if rur > 0.7 else ("ACCEPTABLE" if rur >= 0.5 else ("WARNING" if rur >= 0.3 else "CRITICAL"))
    }


def compute_go_percent(governance_tokens: int, productive_tokens: int) -> Dict:
    """Compute Governance Overhead %."""
    total_tokens = governance_tokens + productive_tokens
    
    go_percent = (governance_tokens / total_tokens * 100) if total_tokens > 0 else 0.0
    
    return {
        "go_percent": round(go_percent, 2),
        "governance_tokens": governance_tokens,
        "productive_tokens": productive_tokens,
        "ratio": "EXCELLENT" if go_percent < 10 else ("HEALTHY" if go_percent < 20 else ("HEAVY" if go_percent < 35 else "COLLAPSE"))
    }


def run_all_ceg_metrics(context_info: Dict) -> Dict:
    """Run all CEG metrics."""
    metrics = {
        "rur": compute_rur(
            retrieved_ids=context_info.get("retrieved_ids", []),
            reasoning_reference_ids=context_info.get("reasoning_referenced_ids", [])
        ),
        "go_percent": compute_go_percent(
            governance_tokens=context_info.get("governance_tokens", 0),
            productive_tokens=context_info.get("productive_tokens", 0)
        )
    }
    
    return metrics


if __name__ == "__main__":
    # Demo
    demo_context = {
        "retrieved_ids": ["mem_001", "mem_002", "mem_003", "mem_004", "mem_005"],
        "reasoning_referenced_ids": ["mem_001", "mem_003", "mem_005"],
        "governance_tokens": 1000,
        "productive_tokens": 8000
    }
    
    metrics = run_all_ceg_metrics(demo_context)
    print(f"RUR: {metrics['rur']['rur']}")
    print(f"GO%: {metrics['go_percent']['go_percent']}")
