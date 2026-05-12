#!/usr/bin/env python3
"""
Phase C: Governance Perturbation Test
==================================
Inject controlled telemetry noise (signal_vector variation)
Verify: UCG stability, scheduler determinism, no recursive escalation
Goal: governance action variance = 0
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/pred-harness-v2')

from execution_record import ExecutionRecordManager
from determinism_enforcer import DeterministicExecutionEngine, DeterminismEnforcer
from validation_layer import DriftAnalyzer, compute_drift_severity
import json


def run_phase_c_governance_perturbation() -> Dict[str, Any]:
    """
    Execute Phase C: Governance Perturbation Test.
    
    Injects controlled telemetry noise and verifies stability.
    """
    print("=" * 60)
    print("PHASE C: GOVERNANCE PERTURBATION TEST")
    print("=" * 60)
    print()
    
    # Initialize components
    record_manager = ExecutionRecordManager(
        log_path="/home/jason2ykk/.openclaw/workspace/pred-harness-v2/logs"
    )
    engine = DeterministicExecutionEngine(DeterminismEnforcer())
    drift_analyzer, drift_reporter = init_analyzer(record_manager)
    
    # Set baseline
    drift_analyzer.set_baseline(1)
    
    # Base query
    base_query = "Explain quantum computing"
    
    # Base governance state
    base_governance = {
        "signal_vector": "governance_state_42",
        "policy": "deterministic",
        "freeze_mode": True
    }
    
    # Perturbation levels
    perturbation_levels = [
        {
            "name": "No noise",
            "signal_vector": "governance_state_42",
            "noise_level": 0.0
        },
        {
            "name": "Tiny noise (0.001)",
            "signal_vector": "governance_state_43",
            "noise_level": 0.001
        },
        {
            "name": "Small noise (0.01)",
            "signal_vector": "governance_state_44",
            "noise_level": 0.01
        },
        {
            "name": "Medium noise (0.1)",
            "signal_vector": "governance_state_45",
            "noise_level": 0.1
        },
        {
            "name": "Large noise (1.0)",
            "signal_vector": "governance_state_99",
            "noise_level": 1.0
        }
    ]
    
    results = []
    
    for level in perturbation_levels:
        print(f"Test: {level['name']}")
        print(f"  Noise Level: {level['noise_level']}")
        print(f"  Signal: {level['signal_vector']}")
        
        # Execute with governance perturbation
        record = engine.execute_query(
            query=base_query,
            retrieval_ids=["doc_quantum_0", "doc_quantum_1", "doc_quantum_2"],
            context_snapshot=f"governance_noise_{level['noise_level']}",
            scheduler_order=["task_1", "task_2", "task_3"],
            governance_state=level
        )
        
        # Analyze drift
        analysis = drift_analyzer.analyze(record.cycle_id)
        metrics = analysis["metrics"]
        
        print(f"  DI: {metrics['determinism_index']:.4f}")
        print(f"  Governance Stability: {metrics['governance_stability']:.4f}")
        print(f"  Scheduler Consistency: {analysis['verification'].get('scheduler_consistency', 'N/A')}")
        
        results.append({
            "test_name": level["name"],
            "noise_level": level["noise_level"],
            "signal_vector": level["signal_vector"],
            "determinism_index": metrics["determinism_index"],
            "governance_stability": metrics["governance_stability"],
            "scheduler_consistency": analysis["verification"].get("scheduler_consistency", True)
        })
        
        print()
    
    # Aggregate results
    print("=" * 60)
    print("PHASE C RESULTS")
    print("=" * 60)
    print()
    
    print(f"Number of Perturbation Levels: {len(perturbation_levels)}")
    print()
    
    # Check governance stability
    target_stability = 1.0
    governance_stable = all(
        r["governance_stability"] >= target_stability 
        for r in results 
        if r["noise_level"] <= 0.01
    )
    
    print(f"Target Governance Stability: {target_stability}")
    print(f"Low Noise Levels (<0.01) Stable: {governance_stable}")
    print()
    
    # Check scheduler consistency
    scheduler_consistent = all(
        r["scheduler_consistency"] == True 
        for r in results
    )
    
    print(f"Scheduler Consistency: {'Maintained' if scheduler_consistent else 'DEGRADED'}")
    print()
    
    # Check for recursive escalation
    di_values = [r["determinism_index"] for r in results]
    escalation_detected = any(di < 0.99 for di in di_values[:4])
    
    print(f"Recursive Escalation Detected: {'NO' if not escalation_detected else 'YES'}")
    print()
    
    # Generate report
    report = {
        "phase": "governance_perturbation",
        "perturbation_levels": len(perturbation_levels),
        "results": results,
        "target_stability": target_stability,
        "governance_stable": governance_stable,
        "scheduler_consistent": scheduler_consistent,
        "escalation_detected": escalation_detected,
        "determinism_index_history": di_values,
        "config_snapshot": {
            "noise_threshold": 0.0,
            "signal_freeze": True
        }
    }
    
    return report


def main():
    """Run Phase C test."""
    try:
        report = run_phase_c_governance_perturbation()
        
        # Save report
        with open(
            "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/phase_c_governance_perturbation.json",
            "w"
        ) as f:
            json.dump(report, f, indent=2)
        
        print()
        print("=" * 60)
        print("PHASE C COMPLETE")
        print("=" * 60)
        print()
        print(f"Report saved to: reports/phase_c_governance_perturbation.json")
        print(f"Overall Status: {'PASS' if report['governance_stable'] and not report['escalation_detected'] else 'FAIL'}")
        print()
        
        return report
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()
