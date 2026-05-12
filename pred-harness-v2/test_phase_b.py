#!/usr/bin/env python3
"""
Phase B: Retrieval Perturbation Test
===================================
Introduce tiny retrieval ordering changes (±1 position)
Measure: output sensitivity, governance stability, semantic variance
Goal: bounded divergence (< 0.05 variance)
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/pred-harness-v2')

from execution_record import ExecutionRecordManager
from determinism_enforcer import DeterministicExecutionEngine, DeterminismEnforcer
from validation_layer import DriftAnalyzer, compute_drift_severity
import json
import random


def run_phase_b_retrieval_perturbation() -> Dict[str, Any]:
    """
    Execute Phase B: Retrieval Perturbation Test.
    
    Introduces ±1 position changes in retrieval ordering
    and measures bounded divergence.
    """
    print("=" * 60)
    print("PHASE B: RETRIEVAL PERTURBATION TEST")
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
    
    # Base retrieval list (ordered)
    base_retrieval = [
        "doc_quantum_0",
        "doc_quantum_1", 
        "doc_quantum_2",
        "doc_quantum_3",
        "doc_quantum_4"
    ]
    
    print(f"Base Query: {base_query}")
    print(f"Base Retrieval Order: {base_retrieval}")
    print()
    
    # Test cases with perturbations
    test_cases = [
        {
            "name": "No perturbation",
            "retrieval": base_retrieval[:3],
            "perturbation": 0
        },
        {
            "name": "+1 swap (shift right)",
            "retrieval": base_retrieval[1:4],
            "perturbation": 1
        },
        {
            "name": "-1 swap (shift left)",
            "retrieval": base_retrieval[:2] + [base_retrieval[3]],
            "perturbation": -1
        },
        {
            "name": "Order reversal (2 items)",
            "retrieval": [base_retrieval[3], base_retrieval[0], base_retrieval[1]],
            "perturbation": "reorder"
        },
        {
            "name": "Single item swap",
            "retrieval": [base_retrieval[2], base_retrieval[0], base_retrieval[1]],
            "perturbation": "swap(0,2)"
        }
    ]
    
    results = []
    
    for case in test_cases:
        print(f"Test: {case['name']}")
        print(f"  Perturbation: {case['perturbation']}")
        print(f"  Retrieval: {case['retrieval']}")
        
        # Execute with perturbed retrieval
        record = engine.execute_query(
            query=base_query,
            retrieval_ids=case['retrieval'],
            context_snapshot=f"perturbation_{case['perturbation']}",
            scheduler_order=["task_1", "task_2"]
        )
        
        # Analyze drift
        analysis = drift_analyzer.analyze(record.cycle_id)
        metrics = analysis["metrics"]
        
        print(f"  DI: {metrics['determinism_index']:.4f}")
        print(f"  Governance Stability: {metrics['governance_stability']:.4f}")
        print(f"  Semantic Variance: {metrics['semantic_variance']:.4f}")
        print(f"  Retrieval Hash Variance: {metrics['retrieval_hash_variance']:.4f}")
        
        results.append({
            "test_name": case["name"],
            "perturbation": case["perturbation"],
            "retrieval": case["retrieval"],
            "determinism_index": metrics["determinism_index"],
            "governance_stability": metrics["governance_stability"],
            "semantic_variance": metrics["semantic_variance"],
            "retrieval_hash_variance": metrics["retrieval_hash_variance"]
        })
        
        print()
    
    # Aggregate results
    print("=" * 60)
    print("PHASE B RESULTS")
    print("=" * 60)
    print()
    
    variance_scores = [r["semantic_variance"] for r in results]
    avg_variance = sum(variance_scores) / len(variance_scores) if variance_scores else 0
    
    print(f"Number of Test Cases: {len(test_cases)}")
    print(f"Average Semantic Variance: {avg_variance:.4f}")
    print(f"Max Variance: {max(variance_scores) if variance_scores else 0:.4f}")
    print(f"Min Variance: {min(variance_scores) if variance_scores else 0:.4f}")
    print()
    
    # Check thresholds
    max_variance_threshold = 0.05
    
    variance_within_bounds = all(v <= max_variance_threshold for v in variance_scores)
    
    print(f"Max Allowed Variance: {max_variance_threshold}")
    print(f"All Variances Within Bounds: {variance_within_bounds}")
    print()
    
    # Governance stability check
    governance_stable = all(r["governance_stability"] == 1.0 for r in results)
    
    print(f"Governance Stability: {'1.0 (stable)' if governance_stable else 'DEGRADED'}")
    print()
    
    # Generate report
    report = {
        "phase": "retrieval_perturbation",
        "test_cases": len(test_cases),
        "results": results,
        "average_variance": avg_variance,
        "max_variance": max(variance_scores) if variance_scores else 0,
        "min_variance": min(variance_scores) if variance_scores else 0,
        "max_variance_threshold": max_variance_threshold,
        "variance_within_bounds": variance_within_bounds,
        "governance_stable": governance_stable,
        "config_snapshot": test_cases[0]["retrieval"][0] if test_cases else ""
    }
    
    return report


def main():
    """Run Phase B test."""
    try:
        report = run_phase_b_retrieval_perturbation()
        
        # Save report
        with open(
            "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/phase_b_retrieval_perturbation.json",
            "w"
        ) as f:
            json.dump(report, f, indent=2)
        
        print()
        print("=" * 60)
        print("PHASE B COMPLETE")
        print("=" * 60)
        print()
        print(f"Report saved to: reports/phase_b_retrieval_perturbation.json")
        print(f"Overall Status: {'PASS' if report['variance_within_bounds'] else 'FAIL'}")
        print()
        
        return report
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()
