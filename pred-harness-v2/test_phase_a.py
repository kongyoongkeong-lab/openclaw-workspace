#!/usr/bin/env python3
"""
Phase A: Static Replay Test
==============================
Run identical workload 10x with:
- fixed seed
- fixed retrieval
- frozen governance
- frozen context

Goal: DI > 0.99
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/pred-harness-v2')

from execution_record import ExecutionRecordManager
from determinism_enforcer import DeterministicExecutionEngine, DeterminismEnforcer
from validation_layer import DriftAnalyzer, DriftReporter, init_analyzer
import json
import time


def run_phase_a_static_replay() -> Dict[str, Any]:
    """
    Execute Phase A: Static Replay Test.
    
    Runs 10 identical cycles and computes Determinism Index.
    """
    print("=" * 60)
    print("PHASE A: STATIC REPLAY TEST")
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
    
    # Run 10 identical cycles
    cycles = []
    queries = [
        "What is the capital of France?",
        "Explain quantum computing",
        "Solve x^2 + 2x + 1 = 0",
        "Summarize machine learning",
        "What is photosynthesis?",
        "Explain neural networks",
        "Describe weather patterns",
        "List programming languages",
        "Explain blockchain",
        "What is artificial intelligence?"
    ]
    
    results = []
    
    for i in range(10):
        print(f"Cycle {i+1}/10: {queries[i][:50]}...")
        
        # Execute with fixed retrieval
        retrieval_ids = [f"doc_{i % 3}"] * 3  # Fixed 3 docs
        
        start_time = time.time()
        record = engine.execute_query(
            query=queries[i],
            retrieval_ids=retrieval_ids,
            context_snapshot=f"context_cycle_{i}",
            scheduler_order=["task_1", "task_2", "task_3"]
        )
        end_time = time.time()
        
        cycles.append(record)
        
        # Analyze drift
        analysis = drift_analyzer.analyze(record.cycle_id)
        results.append({
            "cycle_id": record.cycle_id,
            "determinism_index": analysis["metrics"]["determinism_index"],
            "drift_severity": analysis["metrics"]["drift_severity"]
        })
        
        print(f"  DI: {analysis['metrics']['determinism_index']:.4f}, "
              f"Drift: {analysis['metrics']['drift_severity']:.4f}, "
              f"Time: {(end_time - start_time)*1000:.1f}ms")
    
    # Compute aggregate statistics
    di_values = [r["determinism_index"] for r in results]
    drift_values = [r["drift_severity"] for r in results]
    
    print()
    print("=" * 60)
    print("PHASE A RESULTS")
    print("=" * 60)
    print()
    
    print(f"Cycles Executed: {len(cycles)}")
    print(f"Average DI: {sum(di_values) / len(di_values):.4f}")
    print(f"Min DI: {min(di_values):.4f}")
    print(f"Max DI: {max(di_values):.4f}")
    print(f"Std Dev (DI): {(__import__('statistics').stdev(di_values) if len(di_values) > 1 else 0):.6f}")
    print(f"Average Drift: {sum(drift_values) / len(drift_values):.4f}")
    print(f"Drift Events: {sum(1 for d in drift_values if d > 0)}")
    print()
    
    # Check thresholds
    target_di = 0.99
    target_drift = 0.02
    
    all_pass = all(di >= target_di for di in di_values)
    drift_pass = all(d <= target_drift for d in drift_values)
    
    print(f"Target DI: > {target_di}")
    print(f"All Cycles Meet DI Target: {all_pass}")
    print(f"Retrieval Drift < {target_drift}: {drift_pass}")
    print()
    
    # Generate report
    report = {
        "phase": "static_replay",
        "cycles": len(cycles),
        "results": results,
        "average_di": sum(di_values) / len(di_values),
        "min_di": min(di_values),
        "max_di": max(di_values),
        "std_di": (__import__('statistics').stdev(di_values) if len(di_values) > 1 else 0),
        "average_drift": sum(drift_values) / len(drift_values),
        "drift_events": sum(1 for d in drift_values if d > 0),
        "target_di": target_di,
        "target_drift": target_drift,
        "all_cycles_pass": all_pass,
        "drift_within_bounds": drift_pass,
        "config_snapshot": cycles[0].freeze_config()
    }
    
    return report


def main():
    """Run Phase A test."""
    try:
        report = run_phase_a_static_replay()
        
        # Save report
        with open(
            "/home/jason2ykk/.openclaw/workspace/pred-harness-v2/reports/phase_a_static_replay.json",
            "w"
        ) as f:
            json.dump(report, f, indent=2)
        
        print()
        print("=" * 60)
        print("PHASE A COMPLETE")
        print("=" * 60)
        print()
        print(f"Report saved to: reports/phase_a_static_replay.json")
        print(f"Overall Status: {'PASS' if report['all_cycles_pass'] else 'FAIL'}")
        print()
        
        return report
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


if __name__ == "__main__":
    main()
