# Memory Router with CEG Integration
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

# Import CEG modules
import sys
sys.path.insert(0, Path(__file__).parent)
from idle_context_occupancy import run_idle_context_analysis
from telemetry_integration import (
    compute_rur, compute_go_percent, run_all_ceg_metrics,
    tier_telemetry
)


class PentagonMemoryRouter:
    """Memory router with CEG metrics integration."""
    
    def __init__(self):
        self.memory_dir = Path(__file__).parent / "memory"
        self.episodic_file = self.memory_dir / "episodic.jsonl"
        self.semantic_file = self.memory_dir / "semantic.jsonl"
        self.compression_file = self.memory_dir / "compression.jsonl"
    
    def route_to_intel(self, query: str, context_info: Dict = None) -> Dict:
        """Route retrieval task to @intel with RUR tracking."""
        retrieval_task = {
            "task_type": "web_search",
            "query": query,
            "source": "DDG",
            "retrieved_ids": [],  # Will be populated by @intel
        }
        
        # Compute RUR after retrieval
        if context_info and "retrieved_ids" in context_info:
            metrics = compute_rur(
                retrieved_ids=context_info.get("retrieved_ids", []),
                reasoning_reference_ids=context_info.get("reasoning_referenced_ids", [])
            )
            retrieval_task["rur"] = metrics["rur"]
            retrieval_task["rur_ratio"] = metrics["ratio"]
        
        return retrieval_task
    
    def route_to_ops(self, command: str, operation_type: str = "write") -> Dict:
        """Route shell execution to @ops with telemetry logging."""
        operation = {
            "task_type": operation_type,
            "command": command,
            "telemetry": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": "operation",
                "tier": tier_telemetry("operation", datetime.now(timezone.utc).timestamp())
            }
        }
        
        # Log operation to episodic memory
        self._log_operation(operation)
        
        return operation
    
    def route_to_comms(self, message: str, report_type: str = "final") -> Dict:
        """Route formatted output to @comms with GO% tracking."""
        # Track governance overhead
        governance_tokens = 50  # Approximate
        productive_tokens = 450
        
        go_metrics = compute_go_percent(
            governance_tokens=governance_tokens,
            productive_tokens=productive_tokens
        )
        
        report = {
            "task_type": "formatted_output",
            "message": message,
            "report_type": report_type,
            "go_metrics": go_metrics,
            "quality_score": go_metrics["go_percent"]
        }
        
        return report
    
    def route_to_sentinel(self, payload: Dict, check_type: str = "security") -> Dict:
        """Route security check to @sentinel with telemetry logging."""
        sentinel_task = {
            "task_type": "security_check",
            "check_type": check_type,
            "payload": payload,
            "telemetry": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "type": check_type,
                "tier": tier_telemetry(check_type, datetime.now(timezone.utc).timestamp())
            }
        }
        
        # Log security check to episodic memory
        self._log_operation(sentinel_task)
        
        return sentinel_task
    
    def _log_operation(self, operation: Dict):
        """Log operation to episodic memory."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "operation_log",
            "content": json.dumps(operation),
            "referenced_at": 0,  # Will be set by retrieval
            "summary": f"{operation['task_type']}: {operation.get('command', operation.get('message', ''))[:50]}"
        }
        
        with open(self.episodic_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def process_inference_cycle(self, agent_outputs: List[Dict], reasoning_referenced: List[str]) -> Dict:
        """Process inference cycle and compute GO%."""
        
        # Compute RUR for all retrieved content
        all_retrieved_ids = []
        all_referenced_ids = []
        
        for output in agent_outputs:
            if "retrieved_ids" in output:
                all_retrieved_ids.extend(output["retrieved_ids"])
            if "referenced_ids" in output:
                all_referenced_ids.extend(output["referenced_ids"])
        
        # Deduplicate
        all_retrieved_ids = list(set(all_retrieved_ids))
        all_referenced_ids = list(set(all_referenced_ids))
        
        # Compute metrics
        rur_metrics = compute_rur(
            retrieved_ids=all_retrieved_ids,
            reasoning_reference_ids=all_referenced_ids
        )
        
        # Compute governance overhead
        gov_tokens = 500  # Approximate
        prod_tokens = 4500
        
        go_metrics = compute_go_percent(
            governance_tokens=gov_tokens,
            productive_tokens=prod_tokens
        )
        
        # Run idle context analysis
        idle_report = run_idle_context_analysis(current_turn=10)
        
        return {
            "inference_cycle": {
                "rur": rur_metrics["rur"],
                "rur_ratio": rur_metrics["ratio"],
                "go_percent": go_metrics["go_percent"],
                "go_ratio": go_metrics["ratio"]
            },
            "idle_context": {
                "idle_percent": idle_report.idle_percent,
                "idle_slots": idle_report.idle_slots
            }
        }


if __name__ == "__main__":
    # Demo
    router = PentagonMemoryRouter()
    
    # Demo routing
    intel_task = router.route_to_intel("latest AI safety paper", {"retrieved_ids": ["r1", "r2"]})
    print(f"Intel task: {intel_task['task_type']}")
    
    ops_task = router.route_to_ops("git pull upstream", "write")
    print(f"Ops task: {ops_task['task_type']}")
    
    comms_report = router.route_to_comms("Final report ready.", "final")
    print(f"Comms report: {comms_report['task_type']}")
