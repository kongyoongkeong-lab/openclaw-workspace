"""
Determinism Enforcement Rules V2
==================================
Hard requirements for inference, scheduler, and retrieval layers.
"""

import hashlib
import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from execution_record import ExecutionRecordManager


@dataclass
class DeterminismEnforcer:
    """
    Enforces deterministic execution across all layers.
    
    Inference Layer:
    - temperature = 0.0 (mandatory)
    - fixed seed (seed=42, mandatory)
    - fixed retrieval top_k (top_k=3, mandatory)
    - identical context ordering (no dynamic reordering)
    
    Scheduler Layer:
    - deterministic queue ordering (FIFO only)
    - no adaptive arbitration
    - static priority enforcement
    
    Retrieval Layer:
    - stable ranking algorithm (no timestamp weighting)
    - deduplicate retrieval IDs
    - fixed top_k retrieval count
    """
    
    # Inference Layer
    INFERENCER: Dict[str, Any] = field(
        default_factory=lambda: {
            "temperature": 0.0,
            "seed": 42,
            "top_k": 3,
            "context_ordering": "static",
            "no_dynamic_reordering": True
        }
    )
    
    # Scheduler Layer
    SCHEDULER: Dict[str, Any] = field(
        default_factory=lambda: {
            "queue_ordering": "fifo",
            "adaptive_arbitration": False,
            "static_priority": True,
            "priority_levels": ["critical", "high", "normal", "low"],
            "priority_weights": [4.0, 3.0, 2.0, 1.0]
        }
    )
    
    # Retrieval Layer
    RETRIEVAL: Dict[str, Any] = field(
        default_factory=lambda: {
            "ranking_algorithm": "stable",
            "no_timestamp_weighting": True,
            "deduplicate_ids": True,
            "fixed_top_k": 3,
            "max_retrieval_count": 3,
            "ranking_fn": "cosine_similarity"
        }
    )
    
    # Governance Layer
    GOVERNANCE: Dict[str, Any] = field(
        default_factory=lambda: {
            "telemetry_noise_threshold": 0.0,
            "signal_vector_freeze": True,
            "governance_hash_required": True,
            "action_variance_allowed": 0
        }
    )
    
    def __post_init__(self):
        """Validate and freeze config."""
        # Validate inference layer
        assert self.INFERENCER["temperature"] == 0.0, \
            "Temperature must be 0.0"
        assert self.INFERENCER["seed"] == 42, \
            "Seed must be 42"
        assert self.INFERENCER["top_k"] == 3, \
            "Top_k must be 3"
        
        # Validate scheduler layer
        assert self.SCHEDULER["queue_ordering"] == "fifo", \
            "Queue ordering must be FIFO"
        assert not self.SCHEDULER["adaptive_arbitration"], \
            "Adaptive arbitration must be disabled"
        
        # Validate retrieval layer
        assert self.RETRIEVAL["deduplicate_ids"], \
            "Must deduplicate retrieval IDs"
        assert self.RETRIEVAL["max_retrieval_count"] == 3, \
            "Max retrieval count must be 3"
    
    def freeze_config(self) -> Dict[str, Any]:
        """Return frozen config snapshot."""
        return {
            "inference": self.INFERENCER,
            "scheduler": self.SCHEDULER,
            "retrieval": self.RETRIEVAL,
            "governance": self.GOVERNANCE
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enforcer_config": self.freeze_config(),
            "rules": {
                "inference": self._rules_for_inference(),
                "scheduler": self._rules_for_scheduler(),
                "retrieval": self._rules_for_retrieval()
            }
        }
    
    def _rules_for_inference(self) -> List[str]:
        """Return inference rules."""
        return [
            f"temperature={self.INFERENCER['temperature']}",
            f"seed={self.INFERENCER['seed']}",
            f"top_k={self.INFERENCER['top_k']}",
            "context_ordering=static"
        ]
    
    def _rules_for_scheduler(self) -> List[str]:
        """Return scheduler rules."""
        return [
            f"queue_ordering={self.SCHEDULER['queue_ordering']}",
            f"adaptive_arbitration={self.SCHEDULER['adaptive_arbitration']}",
            f"static_priority={self.SCHEDULER['static_priority']}"
        ]
    
    def _rules_for_retrieval(self) -> List[str]:
        """Return retrieval rules."""
        return [
            f"ranking_algorithm={self.RETRIEVAL['ranking_algorithm']}",
            f"no_timestamp_weighting={self.RETRIEVAL['no_timestamp_weighting']}",
            f"deduplicate_ids={self.RETRIEVAL['deduplicate_ids']}",
            f"fixed_top_k={self.RETRIEVAL['fixed_top_k']}"
        ]


class DeterministicExecutionEngine:
    """
    Executes queries with determinism enforcement.
    
    Usage:
        engine = DeterministicExecutionEngine()
        record = engine.execute_query("your query here",
                                       retrieval_ids=["id1", "id2", "id3"])
        print(f"Cycle: {record.cycle_id}, DI: {record.di}")
    """
    
    def __init__(self, enforcer: DeterminismEnforcer):
        self.enforcer = enforcer
        self.record_manager = ExecutionRecordManager()
    
    def execute_query(self, 
                      query: str,
                      retrieval_ids: Optional[List[str]] = None,
                      context_snapshot: str = None,
                      scheduler_order: Optional[List[str]] = None) -> ExecutionRecord:
        """
        Execute a query with full determinism enforcement.
        
        Args:
            query: The query to execute
            retrieval_ids: IDs to retrieve (will be deduplicated)
            context_snapshot: Frozen context state
            scheduler_order: Queue ordering for scheduler
            
        Returns:
            ExecutionRecord with all hashes and metrics
        """
        # Enforce retrieval deduplication
        if retrieval_ids:
            seen = set()
            deduplicated = []
            for rid in retrieval_ids:
                if rid not in seen:
                    deduplicated.append(rid)
                    seen.add(rid)
            retrieval_ids = deduplicated[:3]  # Limit to top_k
        
        # Generate deterministic output hash
        output = self._generate_deterministic_output(query, retrieval_ids)
        
        # Create execution record
        record = self.record_manager.new_record(
            output=output,
            retrieval_ids=retrieval_ids or [],
            governance_state=self.enforcer.GOVERNANCE,
            context_snapshot=context_snapshot,
            scheduler_order=scheduler_order or []
        )
        
        return record
    
    def _generate_deterministic_output(self, 
                                        query: str,
                                        retrieval_ids: List[str]) -> str:
        """
        Generate deterministic output from query and retrieval state.
        
        Uses SHA-256 of (query + retrieval_ids) for reproducibility.
        In real implementation, this would be the LLM response.
        """
        data = f"{query}|{','.join(retrieval_ids)}"
        hash_value = hashlib.sha256(data.encode()).hexdigest()[:32]
        return f"OUTPUT:{hash_value}"
    
    def freeze_state(self) -> Dict[str, Any]:
        """Freeze current state for reproducible execution."""
        return {
            "enforcer": self.enforcer.to_dict(),
            "records": self.record_manager.get_immutable_log()
        }


# Global engine instance
engine = DeterministicExecutionEngine(DeterminismEnforcer())
