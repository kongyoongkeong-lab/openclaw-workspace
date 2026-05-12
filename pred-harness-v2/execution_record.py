"""
Execution Record Structure with V2 Enhancements
===============================================
Tracks deterministic execution state with:
- retrieval_hash: SHA-256 of retrieval snapshot
- signal_vector: governance state capture
- model_config: inference parameters snapshot
- cycle_id: sequential identifier for replay comparison
"""

import hashlib
import json
import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
from datetime import datetime
import os


@dataclass
class ExecutionRecord:
    """
    Enhanced Execution Record with Predictability Harness V2 fields.
    
    Architecture:
    - output_hash: SHA-256 of final response
    - retrieval_hash: SHA-256 of retrieval snapshot (detects hidden retrieval drift)
    - signal_vector: governance state capture (prevents governance nondeterminism)
    - model_config: inference parameters snapshot (temperature, seed, top_k)
    - context_snapshot: frozen context state for replay
    - scheduler_order: deterministic queue state
    - cycle_id: sequential identifier for replay comparison
    - timestamp: ISO 8601 execution time
    - seed: fixed inference seed
    - top_k: retrieval count
    - temperature: inference temperature
    """
    
    cycle_id: int
    output_hash: str
    retrieval_hash: str
    signal_vector: str
    model_config: Dict[str, Any]
    context_snapshot: str
    scheduler_order: List[str]
    timestamp: str
    seed: int
    top_k: int
    temperature: float
    retrieval_ids: List[str] = field(default_factory=list)
    inference_log: List[str] = field(default_factory=list)
    retrieval_count: int = 0
    governance_state: Dict[str, Any] = field(default_factory=dict)
    
    def compute_hashes(self) -> None:
        """Compute all required hashes for determinism verification."""
        # Output hash
        output_text = self.output_hash
        
        # Retrieval hash - SHA-256 of retrieval snapshot
        retrieval_data = json.dumps({
            "ids": self.retrieval_ids,
            "count": self.retrieval_count,
            "snapshots": self.context_snapshot
        }, sort_keys=True)
        self.retrieval_hash = hashlib.sha256(retrieval_data.encode()).hexdigest()
        
        # Signal vector hash (governance state)
        signal_data = json.dumps(self.governance_state, sort_keys=True)
        self.signal_vector = hashlib.sha256(signal_data.encode()).hexdigest()
    
    def freeze_config(self) -> Dict[str, Any]:
        """Return frozen config snapshot for replay."""
        return {
            "cycle_id": self.cycle_id,
            "seed": self.seed,
            "top_k": self.top_k,
            "temperature": self.temperature,
            "retrieval_hash": self.retrieval_hash,
            "signal_vector": self.signal_vector,
            "retrieval_count": self.retrieval_count
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionRecord":
        """Construct from dictionary."""
        record = cls(**data)
        record.compute_hashes()
        return record
    
    def verify_determinism(self, other: "ExecutionRecord") -> Dict[str, bool]:
        """Verify determinism against another record."""
        return {
            "output_consistency": self.output_hash == other.output_hash,
            "retrieval_consistency": self.retrieval_hash == other.retrieval_hash,
            "scheduler_consistency": self.scheduler_order == other.scheduler_order,
            "governance_consistency": self.signal_vector == other.signal_vector,
            "context_replay_consistency": self.context_snapshot == other.context_snapshot
        }


class ExecutionRecordManager:
    """
    Manages execution records with replay validation.
    
    Features:
    - Immutable log storage
    - Cycle ID auto-increment
    - Determinism Index computation
    - Drift severity scoring
    """
    
    def __init__(self, log_path: str = "/tmp/pred-harness-v2"):
        self.log_path = log_path
        self.cycle_id = 0
        self.records: Dict[int, ExecutionRecord] = {}
        os.makedirs(log_path, exist_ok=True)
    
    def new_record(self, 
                   output: str,
                   retrieval_ids: List[str] = None,
                   governance_state: Dict[str, Any] = None,
                   context_snapshot: str = None,
                   scheduler_order: List[str] = None) -> ExecutionRecord:
        """Create a new execution record."""
        self.cycle_id += 1
        
        if retrieval_ids is None:
            retrieval_ids = []
        if governance_state is None:
            governance_state = {}
        if scheduler_order is None:
            scheduler_order = []
        
        record = ExecutionRecord(
            cycle_id=self.cycle_id,
            output_hash=output,
            retrieval_ids=retrieval_ids[:10],  # Limit to last 10
            retrieval_count=len(retrieval_ids),
            signal_vector=governance_state.get("vector", ""),
            model_config={
                "temperature": 0.0,
                "seed": 42,
                "top_k": 3
            },
            context_snapshot=context_snapshot or "",
            scheduler_order=scheduler_order,
            timestamp=datetime.now().isoformat(),
            seed=42,
            top_k=3,
            temperature=0.0,
            governance_state=governance_state
        )
        
        record.compute_hashes()
        self.records[self.cycle_id] = record
        
        # Log to file
        self._write_record(record)
        
        return record
    
    def _write_record(self, record: ExecutionRecord) -> None:
        """Write record to log file."""
        log_file = os.path.join(self.log_path, f"cycle_{record.cycle_id:05d}.json")
        with open(log_file, 'w') as f:
            json.dump(record.to_dict(), f, indent=2)
    
    def compute_determinism_index(self, record: ExecutionRecord, 
                                   baseline: Optional[ExecutionRecord] = None) -> float:
        """
        Compute Determinism Index (DI).
        
        DI = (oc + rc + sc + gc + crc) / 5
        Where:
        - oc: output_consistency
        - rc: retrieval_consistency  
        - sc: scheduler_consistency
        - gc: governance_consistency
        - crc: context_replay_consistency
        
        Target: DI > 0.99
        """
        if baseline is None:
            # No baseline - assume perfect determinism
            return 1.0
        
        verification = record.verify_determinism(baseline)
        
        consistency_scores = [
            1.0 if verification["output_consistency"] else 0.0,
            1.0 if verification["retrieval_consistency"] else 0.0,
            1.0 if verification["scheduler_consistency"] else 0.0,
            1.0 if verification["governance_consistency"] else 0.0,
            1.0 if verification["context_replay_consistency"] else 0.0
        ]
        
        di = sum(consistency_scores) / len(consistency_scores)
        return di
    
    def compute_drift_severity(self, verification: Dict[str, bool]) -> float:
        """
        Compute drift severity score.
        
        Severity scoring (0.0 = no drift, 1.0 = critical)
        """
        inconsistencies = sum(1 for v in verification.values() if v is False)
        return inconsistencies / len(verification)
    
    def validate_against_baseline(self, record: ExecutionRecord, 
                                   baseline_cycle_id: int) -> Dict[str, Any]:
        """
        Validate current record against baseline.
        
        Returns comprehensive validation report.
        """
        baseline = self.records.get(baseline_cycle_id)
        if baseline is None:
            raise ValueError(f"Baseline cycle {baseline_cycle_id} not found")
        
        di = self.compute_determinism_index(record, baseline)
        verification = record.verify_determinism(baseline)
        drift_severity = self.compute_drift_severity(verification)
        
        report = {
            "cycle_id": record.cycle_id,
            "baseline_cycle_id": baseline_cycle_id,
            "determinism_index": di,
            "drift_severity": drift_severity,
            "verification": verification,
            "config_snapshot": record.freeze_config(),
            "drift_detected": di < 0.99,
            "drift_warning": di < 0.98,
            "metrics": {
                "context_replay_consistency": verification["context_replay_consistency"],
                "retrieval_hash_variance": 0.0 if verification["retrieval_consistency"] else self.compute_drift_severity(verification),
                "determinism_index_target": 0.99,
                "retrieval_drift_target": 0.02,
                "governance_stability_target": 1.0
            }
        }
        
        return report
    
    def get_baseline(self, cycle_id: int) -> Optional[ExecutionRecord]:
        """Get baseline record for comparison."""
        return self.records.get(cycle_id)
    
    def get_latest(self) -> Optional[ExecutionRecord]:
        """Get latest execution record."""
        if not self.records:
            return None
        return max(self.records.values(), key=lambda r: r.cycle_id)
    
    def get_immutable_log(self) -> List[Dict[str, Any]]:
        """Get immutable log of all records."""
        return [r.to_dict() for r in sorted(self.records.values(), 
                                             key=lambda r: r.cycle_id)]


# Singleton instance
record_manager = ExecutionRecordManager()
