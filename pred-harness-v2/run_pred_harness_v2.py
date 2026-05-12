#!/usr/bin/env python3
"""
Predictability Harness V2 - Main Runner
======================================
Executes all test phases:
- Phase A: Static Replay (10 cycles)
- Phase B: Retrieval Perturbation
- Phase C: Governance Perturbation
- Full Replay Validation

Outputs comprehensive report with DI scores.
"""

import sys
import os
import json
import datetime
import time

sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/pred-harness-v2')

from test_phase_a import run_phase_a_static_replay
from test_phase_b import run_phase_b_retrieval_perturbation
from test_phase_c import run_phase_c_governance_perturbation
from deterministic_replay_validator import DeterministicReplayValidator
from execution_record import ExecutionRecordManager
from determinism_enforcer import DeterministicExecutionEngine, DeterminismEnforcer
from validation_layer import DriftAnalyzer, DriftReporter, init_analyzer


def ensure_directories() -> None:
    """Ensure all directories exist."""
    dirs = [
        "/home/jason2ykk/.openclaw/workspace/pred-harness-v2",
        "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/logs",
        "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def run_all_phases() -> Dict[str, Any]:
    """
    Execute all test phases and compile final report.
    
    Returns comprehensive harness report.
    """
    start_time = time.time()
    
    print("=" * 70)
    print("PREDICTABILITY HARNESS V2 - IMPLEMENTATION")
    print("=" * 70)
    print()
    print(f"Started: {datetime.datetime.now()}")
    print()
    
    # Ensure directories
    ensure_directories()
    
    # Initialize components
    record_manager = ExecutionRecordManager(
        log_path="/home/jason2ykk/.openclaw/workspace/pred-harness-v2/logs"
    )
    engine = DeterministicExecutionEngine(DeterminismEnforcer())
    drift_analyzer, drift_reporter = init_analyzer(record_manager)
    
    # Create baseline
    baseline_record = engine.execute_query(
        query="baseline_query",
        retrieval_ids=["doc_0", "doc_1", "doc_2"],
        context_snapshot="baseline",
        scheduler_order=["task_1", "task_2", "task_3"]
    )
    
    print("=" * 70)
    print("PHASE A: STATIC REPLAY")
    print("=" * 70)
    print()
    
    # Phase A: Static Replay
    phase_a_start = time.time()
    phase_a_report = run_phase_a_static_replay()
    phase_a_time = time.time() - phase_a_start
    
    print()
    print(f"Phase A Time: {phase_a_time:.2f}s")
    
    # Phase B: Retrieval Perturbation
    print()
    print("=" * 70)
    print("PHASE B: RETRIEVAL PERTURBATION")
    print("=" * 70)
    print()
    
    phase_b_start = time.time()
    phase_b_report = run_phase_b_retrieval_perturbation()
    phase_b_time = time.time() - phase_b_start
    
    print()
    print(f"Phase B Time: {phase_b_time:.2f}s")
    
    # Phase C: Governance Perturbation
    print()
    print("=" * 70)
    print("PHASE C: GOVERNANCE PERTURBATION")
    print("=" * 70)
    print()
    
    phase_c_start = time.time()
    phase_c_report = run_phase_c_governance_perturbation()
    phase_c_time = time.time() - phase_c_start
    
    print()
    print(f"Phase C Time: {phase_c_time:.2f}s")
    
    # Full Replay Validation
    print()
    print("=" * 70)
    print("FULL DETERMINISTIC REPLAY VALIDATION")
    print("=" * 70)
    print()
    
    replay_start = time.time()
    
    validator = DeterministicReplayValidator(
        record_manager=record_manager,
        baseline_cycle_id=1,
        di_threshold_warning=0.98,
        di_threshold_critical=0.99
    )
    
    baseline_retrieval = ["doc_0", "doc_1", "doc_2"]
    baseline_context = "baseline"
    
    # Define replay cycles
    cycles = [
        ("What is the capital of France?", ["doc_fr_0", "doc_fr_1", "doc_fr_2"]),
        ("Explain quantum computing", ["doc_qm_0", "doc_qm_1", "doc_qm_2"]),
        ("Solve x^2 + 2x + 1 = 0", ["doc_math_0", "doc_math_1", "doc_math_2"]),
        ("Summarize machine learning", ["doc_ml_0", "doc_ml_1", "doc_ml_2"]),
        ("What is photosynthesis?", ["doc_bio_0", "doc_bio_1", "doc_bio_2"]),
    ]
    
    replay_report = validator.run_full_validation(
        cycles=cycles,
        baseline_retrieval=baseline_retrieval,
        baseline_context=baseline_context
    )
    
    replay_time = time.time() - replay_start
    
    print()
    print(f"Replay Validation Time: {replay_time:.2f}s")
    
    # Compile final report
    total_time = time.time() - start_time
    
    final_report = {
        "harness": "Predictability Harness V2",
        "timestamp": datetime.datetime.now().isoformat(),
        "baseline_cycle": baseline_record.cycle_id,
        "phases": {
            "static_replay": phase_a_report,
            "retrieval_perturbation": phase_b_report,
            "governance_perturbation": phase_c_report
        },
        "replay_validation": replay_report,
        "timing": {
            "phase_a_seconds": phase_a_time,
            "phase_b_seconds": phase_b_time,
            "phase_c_seconds": phase_c_time,
            "replay_seconds": replay_time,
            "total_seconds": total_time
        },
        "summary": {
            "all_phases_passed": (
                phase_a_report.get("all_cycles_pass", False) and
                phase_b_report.get("variance_within_bounds", False) and
                phase_c_report.get("governance_stable", False) and
                phase_c_report.get("scheduler_consistent", False) and
                not phase_c_report.get("escalation_detected", False) and
                replay_report.get("summary", {}).get("all_cycles_ok", False)
            ),
            "average_di": replay_report["summary"].get("average_di", 0),
            "min_di": replay_report["summary"].get("min_di", 0),
            "max_di": replay_report["summary"].get("max_di", 0),
            "di_target": 0.99
        },
        "output_hash": baseline_record.output_hash,
        "retrieval_hash": baseline_record.retrieval_hash,
        "signal_vector": baseline_record.signal_vector,
        "model_config": baseline_record.freeze_config(),
        "config_snapshot": {
            "temperature": 0.0,
            "seed": 42,
            "top_k": 3
        },
        "metrics": {
            "determinism_index": replay_report["summary"]["average_di"],
            "retrieval_drift": replay_report["summary"].get("min_di", 0),
            "governance_stability": 1.0
        }
    }
    
    # Save report
    report_path = "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/pred-harness-v2_final_report.json"
    with open(report_path, "w") as f:
        json.dump(final_report, f, indent=2)
    
    print()
    print("=" * 70)
    print("EXECUTION COMPLETE")
    print("=" * 70)
    print()
    print(f"Total Time: {total_time:.2f}s")
    print()
    print(f"Average DI: {replay_report['summary']['average_di']:.4f}")
    print(f"DI Target: 0.99")
    print(f"All Cycles OK: {replay_report['summary']['all_cycles_ok']}")
    print()
    print(f"Final Report: {report_path}")
    print()
    print(f"Output Hash: {baseline_record.output_hash}")
    print(f"Retrieval Hash: {baseline_record.retrieval_hash}")
    print(f"Signal Vector: {baseline_record.signal_vector}")
    print()
    
    return final_report


def main():
    """Main entry point."""
    try:
        report = run_all_phases()
        
        # Print summary
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print()
        print(f"Harness: {report['harness']}")
        print(f"Timestamp: {report['timestamp']}")
        print()
        print("PHASES:")
        print(f"  Static Replay: {'PASS' if report['phases']['static_replay'].get('all_cycles_pass', False) else 'FAIL'}")
        print(f"  Retrieval Perturbation: {'PASS' if report['phases']['retrieval_perturbation'].get('variance_within_bounds', False) else 'FAIL'}")
        print(f"  Governance Perturbation: {'PASS' if report['phases']['governance_perturbation'].get('governance_stable', False) else 'FAIL'}")
        print()
        print(f"FINAL DI: {report['summary']['average_di']:.4f}")
        print(f"OVERALL STATUS: {'PASS' if report['summary']['all_phases_passed'] else 'FAIL'}")
        print()
        
        return report
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()
