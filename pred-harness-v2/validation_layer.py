"""
Validation Layer V2
==================
Implements drift severity scoring and validation functions.
"""

import hashlib
from typing import Any, Dict, List, Optional, Tuple
from execution_record import ExecutionRecord, ExecutionRecordManager
from scipy.spatial.distance import cosine  # type: ignore


def validate_determinism(rec1: ExecutionRecord, 
                          rec2: ExecutionRecord) -> Dict[str, Any]:
    """
    Validate determinism between two execution records.
    
    Returns comprehensive verification report.
    """
    verification = {
        "output_consistency": rec1.output_hash == rec2.output_hash,
        "retrieval_consistency": rec1.retrieval_hash == rec2.retrieval_hash,
        "scheduler_consistency": rec1.scheduler_order == rec2.scheduler_order,
        "governance_consistency": rec1.signal_vector == rec2.signal_vector,
        "context_replay_consistency": rec1.context_snapshot == rec2.context_snapshot,
        "semantic_equivalence": _compute_semantic_similarity(rec1.output_hash, rec2.output_hash),
        "drift_severity": compute_drift_severity(verification)
    }
    
    return verification


def compute_drift_severity(consistency_dict: Dict[str, bool]) -> float:
    """
    Severity scoring (0.0 = no drift, 1.0 = critical)
    
    Severity = (number of inconsistencies) / (total checks)
    """
    if not consistency_dict:
        return 0.0
    
    inconsistencies = sum(1 for v in consistency_dict.values() if v is False)
    total_checks = len(consistency_dict)
    
    severity = inconsistencies / total_checks if total_checks > 0 else 0.0
    
    # Clamp to valid range
    severity = max(0.0, min(1.0, severity))
    
    return severity


def _compute_semantic_similarity(hash1: str, hash2: str) -> float:
    """
    Compute semantic equivalence using hash similarity.
    
    For production, use vector embeddings.
    """
    if hash1 == hash2:
        return 1.0
    
    # Simple hash-based similarity
    len1, len2 = len(hash1), len(hash2)
    
    # Character-level similarity
    matches = 0
    for c1, c2 in zip(hash1, hash2):
        if c1 == c2:
            matches += 1
    
    similarity = matches / max(len1, len2) if max(len1, len2) > 0 else 0.0
    
    return min(1.0, similarity)


class DriftAnalyzer:
    """
    Analyzes and tracks drift over execution cycles.
    
    Metrics:
    - ContextReplayConsistency: identical context reconstruction (target: 1.0)
    - RetrievalHashVariance: retrieval state divergence (target: < 0.02)
    - DeterminismIndex (DI): (oc + rc + sc + gc + crc) / 5 (target: > 0.99)
    """
    
    def __init__(self, record_manager: ExecutionRecordManager):
        self.record_manager = record_manager
        self.baseline_cycle_id: Optional[int] = None
        self.drift_history: List[Dict[str, Any]] = []
    
    def set_baseline(self, cycle_id: int) -> None:
        """Set baseline for comparison."""
        self.baseline_cycle_id = cycle_id
    
    def analyze(self, cycle_id: int) -> Dict[str, Any]:
        """
        Analyze drift for a given cycle.
        
        Returns comprehensive drift analysis.
        """
        record = self.record_manager.get_latest()
        if record is None:
            return self._empty_analysis()
        
        baseline = None
        if self.baseline_cycle_id is not None:
            baseline = self.record_manager.get_baseline(self.baseline_cycle_id)
        
        verification = validate_determinism(baseline, record) if baseline else {"all": True}
        
        # Compute metrics
        metrics = self._compute_metrics(verification, record)
        
        # Track history
        analysis = {
            "cycle_id": cycle_id,
            "baseline_cycle_id": self.baseline_cycle_id,
            "metrics": metrics,
            "determinism_index": metrics["determinism_index"],
            "drift_severity": metrics["drift_severity"],
            "drift_detected": metrics["drift_severity"] > 0.02,
            "drift_warning": metrics["determinism_index"] < 0.99,
            "critical": metrics["drift_severity"] > 0.9
        }
        
        self.drift_history.append(analysis)
        
        return analysis
    
    def _compute_metrics(self, 
                          verification: Dict[str, bool],
                          record: ExecutionRecord) -> Dict[str, Any]:
        """Compute all determinism metrics."""
        
        # Extract consistency values
        oc = verification.get("output_consistency", True)
        rc = verification.get("retrieval_consistency", True)
        sc = verification.get("scheduler_consistency", True)
        gc = verification.get("governance_consistency", True)
        crc = verification.get("context_replay_consistency", True)
        semantic = verification.get("semantic_equivalence", True)
        
        # Determinism Index (DI)
        di = (oc + rc + sc + gc + crc) / 5.0
        
        # Context Replay Consistency
        context_replay_consistency = crc
        
        # Retrieval Hash Variance
        retrieval_drift = 0.0 if rc else compute_drift_severity({"retrieval": not rc})
        
        # Governance Stability
        governance_stability = 1.0 if gc else 0.0
        
        # Output consistency
        output_consistency = oc
        
        # Semantic variance
        semantic_variance = 1.0 - semantic if semantic else 1.0
        
        return {
            "context_replay_consistency": context_replay_consistency,
            "retrieval_hash_variance": retrieval_drift,
            "determinism_index": di,
            "governance_stability": governance_stability,
            "output_consistency": output_consistency,
            "semantic_variance": semantic_variance
        }
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Return empty analysis structure."""
        return {
            "cycle_id": 0,
            "baseline_cycle_id": None,
            "metrics": {},
            "determinism_index": 0.0,
            "drift_severity": 0.0,
            "drift_detected": False,
            "drift_warning": False,
            "critical": False
        }


class DriftReporter:
    """
    Generates drift reports when DI drops below thresholds.
    """
    
    def __init__(self, record_manager: ExecutionRecordManager):
        self.record_manager = record_manager
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive drift report."""
        latest = self.record_manager.get_latest()
        if latest is None:
            return {"error": "No records found"}
        
        report = {
            "report_type": "drift_analysis",
            "generated_at": latest.timestamp,
            "cycle_id": latest.cycle_id,
            "status": "healthy" if latest.drift_severity < 0.05 else "warning",
            "critical": latest.drift_severity > 0.9,
            "metrics": {
                "determinism_index": latest.di,
                "retrieval_drift": latest.retrieval_hash_variance,
                "governance_stability": latest.governance_stability,
                "context_replay_consistency": latest.context_replay_consistency
            },
            "config_snapshot": latest.freeze_config(),
            "recommendations": self._generate_recommendations(latest),
            "history": self.record_manager.get_immutable_log()[-10:] if hasattr(latest, 'history') else []
        }
        
        return report
    
    def _generate_recommendations(self, record: ExecutionRecord) -> List[str]:
        """Generate recommendations based on drift state."""
        recommendations = []
        
        if record.drift_severity > 0.5:
            recommendations.append("CRITICAL: High drift detected. Freeze all state.")
        
        if record.retrieval_drift > 0.02:
            recommendations.append("Retrieval layer showing variance. Check ranking algorithm.")
        
        if record.context_replay_consistency < 1.0:
            recommendations.append("Context reconstruction drifting. Verify context snapshot.")
        
        if record.governance_stability < 1.0:
            recommendations.append("Governance state changing. Inject noise threshold too high.")
        
        if not recommendations:
            recommendations.append("System operating within determinism bounds.")
        
        return recommendations


# Global analyzer instance
drift_analyzer = None
drift_reporter = None


def init_analyzer(record_manager: ExecutionRecordManager) -> Tuple[DriftAnalyzer, DriftReporter]:
    """Initialize global analyzer and reporter."""
    global drift_analyzer, drift_reporter
    
    drift_analyzer = DriftAnalyzer(record_manager)
    drift_reporter = DriftReporter(record_manager)
    
    return drift_analyzer, drift_reporter
