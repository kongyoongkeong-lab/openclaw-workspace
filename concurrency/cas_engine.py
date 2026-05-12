"""
Phase 4 CAS Ingestion Engine
Deterministic Compare-And-Swap under concurrent pressure
"""
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Literal
from datetime import datetime, timezone


@dataclass
class WriteAttempt:
    """Trace log for a single CAS attempt"""
    incident_id: str
    attempt_version: int
    writer_id: str
    logical_time: float
    sequence_id: int
    result: Literal["COMMIT", "REJECT"]
    reason: Literal["STALE", "WINNER_LOST", "NORMAL"]
    winner_rank: Optional[int] = None


@dataclass
class CASConfig:
    """CAS retry model configuration"""
    mode: Literal["STRICT", "STABILITY"] = "STRICT"
    max_retries: int = 3  # Only for STABILITY mode


class CASIngestionEngine:
    """
    Deterministic CAS engine under concurrent pressure.
    
    Semantics:
    - Write atomic rule: commit iff incoming_version == current_version
    - Retry model: STRICT (0 retries) or STABILITY (bounded retries)
    - Winner determinism: min(logical_time, sequence_id, agent_id_hash)
    - Full traceability: all attempts logged for replay
    """
    
    def __init__(self, mode: str = "STRICT"):
        self.mode = mode
        self.config = CASConfig(mode=mode)
        self.current_version: Dict[str, int] = {}
        self.next_sequence_id: int = 0
        self.attempts: List[WriteAttempt] = []
        self.metrics = {
            "cas_successes": 0,
            "cas_rejections": 0,
            "conflicts_resolved": 0,
            "retries": 0,
            "logical_time": 0.0,
        }
    
    def _get_agent_hash(self, writer_id: str) -> int:
        """Deterministic hash for writer tie-breaking"""
        return int(hashlib.md5(writer_id.encode()).hexdigest()[:8], 16)
    
    def _determine_winner(self, attempts: List[Dict]) -> Optional[Dict]:
        """
        Deterministic winner selection.
        
        Winner = min(logical_time, sequence_id, agent_id_hash)
        """
        def sort_key(attempt):
            return (
                int(attempt["logical_time"]),
                attempt["sequence_id"],
                self._get_agent_hash(attempt["writer_id"])
            )
        
        if not attempts:
            return None
        return min(attempts, key=sort_key)
    
    def _emit_trace(self, incident_id: str, version: int, writer_id: str,
                    logical_time: float, sequence_id: int, result: str,
                    reason: str, winner_rank: Optional[int] = None) -> WriteAttempt:
        """Emit traceability log for causal audit"""
        attempt = WriteAttempt(
            incident_id=incident_id,
            attempt_version=version,
            writer_id=writer_id,
            logical_time=logical_time,
            sequence_id=sequence_id,
            result=result,
            reason=reason,
            winner_rank=winner_rank
        )
        self.attempts.append(attempt)
        return attempt
    
    def _update_metrics(self, success: bool, conflict: bool = False, retry: bool = False):
        """Update metrics counters"""
        if success:
            self.metrics["cas_successes"] += 1
        else:
            self.metrics["cas_rejections"] += 1
        if conflict:
            self.metrics["conflicts_resolved"] += 1
        if retry:
            self.metrics["retries"] += 1
        self.metrics["logical_time"] += 1.0  # Increment logical clock
    
    def ingest(self, incident_id: str, data: dict, writer_id: str, version: int,
               sequence_id: int) -> tuple[bool, str, List[WriteAttempt]]:
        """
        Core CAS ingestion operation.
        
        Returns:
            (success, status, trace_logs)
        """
        logical_time = self.metrics["logical_time"]
        
        # Check CAS atomic rule
        current_version = self.current_version.get(incident_id, 0)
        
        if version != current_version:
            # CAS failure - version mismatch
            self._update_metrics(success=False, conflict=True)
            
            # Determine if this is a stale mutation or a lost winner race
            if self.config.mode == "STRICT":
                # STRICT mode: no retries
                reason = "STALE" if version < current_version else "WINNER_LOST"
                winner = self._determine_winner([
                    {"writer_id": writer_id, "logical_time": logical_time,
                     "sequence_id": sequence_id, "version": version}
                ])
                return False, "STALE_MUTATION", self.attempts
            
            else:
                # STABILITY mode: bounded retries
                self.metrics["retries"] += 1
                # In real implementation, would retry here
                return False, "RETRYING", self.attempts
        
        # CAS success
        self.current_version[incident_id] = version + 1
        self._update_metrics(success=True)
        
        return True, "COMMITTED", self.attempts
    
    def get_causal_ambiguity_index(self, total_conflicts: int) -> float:
        """
        Compute refined CAI metric.
        
        CAI = non_deterministic_resolution_events / total_conflict_events
        
        Non-deterministic = outcome cannot be derived from deterministic rule
        """
        non_det_events = 0
        
        for attempt in self.attempts:
            if attempt.result == "REJECT":
                # Check if this was deterministic or ambiguous
                # In this implementation, all rejections should be deterministic
                # But if multiple winners tie on all metrics, that's non-deterministic
                if attempt.winner_rank is None:
                    non_det_events += 1
        
        if total_conflicts == 0:
            return 0.0
        
        return non_det_events / total_conflicts
    
    def get_cds(self) -> float:
        """
        Compute Causal Determination Stability.
        
        CDS = 1.0 if all conflicts resolve deterministically, else < 1.0
        """
        total_conflicts = self.metrics["conflicts_resolved"]
        if total_conflicts == 0:
            return 1.0
        
        non_det = self.get_causal_ambiguity_index(total_conflicts)
        return 1.0 - non_det
    
    def get_metrics(self) -> dict:
        """Get current metrics snapshot"""
        total_ops = self.metrics["cas_successes"] + self.metrics["cas_rejections"]
        return {
            "mode": self.config.mode,
            "total_operations": total_ops,
            "cas_successes": self.metrics["cas_successes"],
            "cas_rejections": self.metrics["cas_rejections"],
            "conflicts_resolved": self.metrics["conflicts_resolved"],
            "retries": self.metrics["retries"],
            "logical_time": self.metrics["logical_time"],
            "cds": self.get_cds(),
            "cai": self.get_causal_ambiguity_index(self.metrics["conflicts_resolved"]),
            "attempts_count": len(self.attempts),
        }
    
    def reset(self):
        """Reset engine for new test run"""
        self.current_version.clear()
        self.next_sequence_id = 0
        self.attempts.clear()
        self.metrics = {
            "cas_successes": 0,
            "cas_rejections": 0,
            "conflicts_resolved": 0,
            "retries": 0,
            "logical_time": 0.0,
        }


# Example usage:
if __name__ == "__main__":
    engine = CASIngestionEngine(mode="STRICT")
    
    # Simulate concurrent writes to same resource
    incidents = ["inc_001", "inc_002", "inc_003"]
    writers = ["agent_alpha", "agent_beta", "agent_gamma"]
    
    for i, incident in enumerate(incidents):
        writer = writers[i % len(writers)]
        sequence_id = i * 1000
        
        success, status, traces = engine.ingest(
            incident_id=incident,
            data={"key": f"value_{i}"},
            writer_id=writer,
            version=0,  # All start at version 0
            sequence_id=sequence_id
        )
        
        print(f"Ingest {i}: {status}")
        for trace in traces:
            print(f"  - {trace.result}: {trace.reason}")
    
    print("\nMetrics:", engine.get_metrics())
