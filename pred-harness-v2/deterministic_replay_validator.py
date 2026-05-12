#!/usr/bin/env python3
"""
Deterministic Replay Validator V2
===============================
Records all execution_records in immutable log
Computes DI after each cycle
Flags any DI drop below 0.99
Generates drift report if DI < 0.98
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/pred-harness-v2')

from execution_record import ExecutionRecordManager
from determinism_enforcer import DeterministicExecutionEngine, DeterminismEnforcer
from validation_layer import DriftAnalyzer, DriftReporter, init_analyzer
import json
import os


class DeterministicReplayValidator:
    """
    Validates deterministic execution across replay cycles.
    
    Responsibilities:
    - Record all execution_records in immutable log
    - Compute DI after each cycle
    - Flag any DI drop below 0.99
    - Generate drift report if DI < 0.98
    """
    
    def __init__(self, 
                 record_manager: ExecutionRecordManager,
                 baseline_cycle_id: int = 1,
                 di_threshold_warning: float = 0.98,
                 di_threshold_critical: float = 0.99):
        self.record_manager = record_manager
        self.baseline_cycle_id = baseline_cycle_id
        self.di_threshold_warning = di_threshold_warning
        self.di_threshold_critical = di_threshold_critical
        self.drift_analyzer = DriftAnalyzer(record_manager)
        self.drift_reporter = DriftReporter(record_manager)
        self.drift_analyzer.set_baseline(baseline_cycle_id)
        self.history: list = []
        self.flags: list = []
        self.reports: list = []
    
    def validate_cycle(self, 
                       record,
                       query: str = None) -> Dict[str, Any]:
        """
        Validate a single cycle against baseline.
        
        Args:
            record: ExecutionRecord to validate
            query: Original query (for context)
            
        Returns:
            Validation result with flags
        """
        # Analyze drift
        analysis = self.drift_analyzer.analyze(record.cycle_id)
        
        # Check thresholds
        di = analysis["metrics"]["determinism_index"]
        drift = analysis["metrics"]["drift_severity"]
        
        validation = {
            "cycle_id": record.cycle_id,
            "determinism_index": di,
            "drift_severity": drift,
            "status": "ok",
            "flags": []
        }
        
        # Check warning threshold (DI < 0.98)
        if di < self.di_threshold_warning:
            validation["status"] = "warning"
            validation["flags"].append(
                f"DI dropped below warning threshold: {di:.4f} < {self.di_threshold_warning}"
            )
            self.flags.append({
                "cycle_id": record.cycle_id,
                "severity": "warning",
                "message": f"DI critical drop: {di:.4f}",
                "di": di
            })
        
        # Check critical threshold (DI < 0.99)
        elif di < self.di_threshold_critical:
            validation["status"] = "critical"
            validation["flags"].append(
                f"DI dropped below critical threshold: {di:.4f} < {self.di_threshold_critical}"
            )
        
        # Check drift severity
        if drift > 0.1:
            validation["flags"].append(
                f"High drift severity: {drift:.4f} > 0.1"
            )
        
        self.history.append({
            "cycle_id": record.cycle_id,
            "query": query,
            "determinism_index": di,
            "drift_severity": drift,
            "status": validation["status"],
            "flags": validation["flags"]
        })
        
        return validation
    
    def replay_cycle(self, 
                     query: str,
                     retrieval_ids: list,
                     context_snapshot: str = None) -> Dict[str, Any]:
        """
        Replay a cycle with deterministic parameters.
        
        Args:
            query: Query to execute
            retrieval_ids: Retrieval IDs (fixed)
            context_snapshot: Frozen context
            
        Returns:
            Cycle replay result
        """
        record = self.record_manager.new_record(
            output=f"output_for_{hash(query)}",
            retrieval_ids=retrieval_ids,
            governance_state={"freeze_mode": True},
            context_snapshot=context_snapshot
        )
        
        validation = self.validate_cycle(record, query=query)
        
        return {
            "cycle_id": record.cycle_id,
            "query": query,
            "record": record,
            "validation": validation
        }
    
    def run_immutable_log() -> list:
        """Get immutable log of all records."""
        return self.record_manager.get_immutable_log()
    
    def generate_drift_report(self) -> Dict[str, Any]:
        """
        Generate drift report if DI < 0.98.
        
        Returns:
            Drift report or None if no drift detected
        """
        latest = self.record_manager.get_latest()
        if latest is None:
            return None
        
        latest_di = self.history[-1]["determinism_index"] if self.history else 1.0
        
        if latest_di < self.di_threshold_warning:
            report = {
                "report_type": "drift_alert",
                "generated_at": latest.timestamp,
                "cycle_id": latest.cycle_id,
                "determinism_index": latest_di,
                "status": "critical",
                "message": f"DETERMINISM INDEX CRITICAL: {latest_di:.4f}",
                "recommendations": self._generate_recommendations(latest),
                "immutable_log": self.run_immutable_log(),
                "flags": self.flags
            }
            
            # Save report
            report_path = f"/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/drift_{latest.cycle_id}.json"
            with open(report_path, "w") as f:
                json.dump(report, f, indent=2)
            
            print(f"Drift report saved: {report_path}")
            
            return report
        elif latest_di < self.di_threshold_critical:
            report = {
                "report_type": "drift_warning",
                "generated_at": latest.timestamp,
                "cycle_id": latest.cycle_id,
                "determinism_index": latest_di,
                "status": "warning",
                "message": f"DETERMINISM INDEX WARNING: {latest_di:.4f}"
            }
            
            return report
        
        return None
    
    def _generate_recommendations(self, record) -> list:
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
    
    def run_full_validation(self, 
                           cycles: list,
                           baseline_retrieval: list = None,
                           baseline_context: str = None) -> Dict[str, Any]:
        """
        Run full validation across multiple cycles.
        
        Args:
            cycles: List of cycles to replay
            baseline_retrieval: Baseline retrieval IDs
            baseline_context: Baseline context snapshot
            
        Returns:
            Full validation report
        """
        if baseline_retrieval is None:
            baseline_retrieval = ["doc_0", "doc_1", "doc_2"]
        if baseline_context is None:
            baseline_context = "baseline_context"
        
        print("=" * 60)
        print("DETERMINISTIC REPLAY VALIDATION")
        print("=" * 60)
        print()
        
        # Replay all cycles
        results = []
        for i, (query, retrieval_ids) in enumerate(cycles):
            print(f"Replaying cycle {i+1}/{len(cycles)}...")
            
            context_snapshot = baseline_context
            if isinstance(query, dict):
                context_snapshot = query.get("context", baseline_context)
            
            result = self.replay_cycle(
                query=query,
                retrieval_ids=retrieval_ids,
                context_snapshot=context_snapshot
            )
            
            results.append(result)
            
            di = result["validation"]["determinism_index"]
            status = result["validation"]["status"]
            flags = result["validation"]["flags"]
            
            print(f"  Cycle {i+1}: DI={di:.4f}, Status={status}")
            if flags:
                for flag in flags:
                    print(f"    - {flag}")
            print()
        
        # Generate drift report if needed
        drift_report = self.generate_drift_report()
        
        # Compile full report
        full_report = {
            "validation_type": "deterministic_replay",
            "cycles_replayed": len(cycles),
            "results": results,
            "drift_report": drift_report,
            "summary": self._compile_summary(results)
        }
        
        return full_report
    
    def _compile_summary(self, results: list) -> Dict[str, Any]:
        """Compile validation summary."""
        di_values = [r["validation"]["determinism_index"] for r in results]
        status_counts = {}
        flag_counts = {}
        
        for r in results:
            status = r["validation"]["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            
            for flag in r["validation"]["flags"]:
                flag_counts[flag] = flag_counts.get(flag, 0) + 1
        
        return {
            "total_cycles": len(results),
            "average_di": sum(di_values) / len(di_values) if di_values else 0,
            "min_di": min(di_values) if di_values else 0,
            "max_di": max(di_values) if di_values else 0,
            "status_distribution": status_counts,
            "flag_distribution": flag_counts,
            "all_cycles_ok": all(
                r["validation"]["determinism_index"] >= self.di_threshold_critical
                for r in results
            )
        }


def main():
    """Run deterministic replay validator."""
    try:
        # Initialize components
        record_manager = ExecutionRecordManager(
            log_path="/home/jason2ykk/.openclaw/workspace/pred-harness-v2/logs"
        )
        engine = DeterministicExecutionEngine(DeterminismEnforcer())
        validator = DeterministicReplayValidator(
            record_manager=record_manager,
            baseline_cycle_id=1,
            di_threshold_warning=0.98,
            di_threshold_critical=0.99
        )
        
        # Baseline retrieval
        baseline_retrieval = ["doc_quantum_0", "doc_quantum_1", "doc_quantum_2"]
        baseline_context = "baseline_context_42"
        
        # Define cycles to replay
        cycles = [
            (
                "What is the capital of France?",
                ["doc_france_0", "doc_france_1", "doc_france_2"]
            ),
            (
                "Explain quantum computing",
                ["doc_quantum_0", "doc_quantum_1", "doc_quantum_2"]
            ),
            (
                "Solve x^2 + 2x + 1 = 0",
                ["doc_math_0", "doc_math_1", "doc_math_2"]
            ),
            (
                "Summarize machine learning",
                ["doc_ml_0", "doc_ml_1", "doc_ml_2"]
            ),
            (
                "What is photosynthesis?",
                ["doc_bio_0", "doc_bio_1", "doc_bio_2"]
            )
        ]
        
        # Run full validation
        report = validator.run_full_validation(
            cycles=cycles,
            baseline_retrieval=baseline_retrieval,
            baseline_context=baseline_context
        )
        
        # Save report
        with open(
            "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/deterministic_replay_validation.json",
            "w"
        ) as f:
            json.dump(report, f, indent=2)
        
        print()
        print("=" * 60)
        print("DETERMINISTIC REPLAY VALIDATION COMPLETE")
        print("=" * 60)
        print()
        print(f"Cycles Replayed: {report['cycles_replayed']}")
        print(f"Average DI: {report['summary']['average_di']:.4f}")
        print(f"All Cycles OK: {report['summary']['all_cycles_ok']}")
        print()
        print(f"Report saved to: reports/deterministic_replay_validation.json")
        print()
        
        return report
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()
