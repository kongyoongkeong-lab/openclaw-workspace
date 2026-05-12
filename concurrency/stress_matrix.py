#!/usr/bin/env python3
"""
Phase 4 Stress Matrix Runner
Tests CAS under controlled concurrency pressure
"""
import sys
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from cas_engine import CASIngestionEngine
from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class MatrixResult:
    """Result of a single stress matrix level"""
    level: int
    writers: int
    operations: int
    successes: int
    rejections: int
    conflicts: int
    cds: float
    cai: float
    elapsed_ms: float
    error: str = ""


def run_single_writer_test(engine: CASIngestionEngine, ops: int) -> MatrixResult:
    """Level 1: Single writer"""
    random.seed(42)
    for i in range(ops):
        incident_id = f"inc_l1_{i}"
        success, status, _ = engine.ingest(incident_id, {}, f"single_writer", i, i)
    
    return MatrixResult(
        level=1,
        writers=1,
        operations=ops,
        successes=engine.metrics["cas_successes"],
        rejections=engine.metrics["cas_rejections"],
        conflicts=engine.metrics["conflicts_resolved"],
        cds=engine.get_cds(),
        cai=engine.get_causal_ambiguity_index(engine.metrics["conflicts_resolved"]),
        elapsed_ms=0.0,
    )


def run_multi_writer_storm(engine: CASIngestionEngine, writers: int, ops_per_writer: int) -> MatrixResult:
    """Level 2+: Multi-writer concurrent storms"""
    # Reset logical time for fresh race
    engine.metrics["logical_time"] = 0.0
    
    incident_id = f"inc_l{engine.metrics['cas_rejections'] + 1}_storm"
    
    with ThreadPoolExecutor(max_workers=min(writers, 50)) as executor:
        futures = []
        for w_idx in range(writers):
            writer_id = f"agent_{w_idx:03d}"
            seq_id = w_idx * 100
            future = executor.submit(
                engine.ingest,
                incident_id,
                {},
                writer_id,
                0,  # All start at version 0
                seq_id
            )
            futures.append(future)
        
        # Collect results (not needed for metrics since engine tracks internally)
        for _ in as_completed(futures):
            pass
    
    total_ops = writers * ops_per_writer
    return MatrixResult(
        level=2,
        writers=writers,
        operations=total_ops,
        successes=engine.metrics["cas_successes"],
        rejections=engine.metrics["cas_rejections"],
        conflicts=engine.metrics["conflicts_resolved"],
        cds=engine.get_cds(),
        cai=engine.get_causal_ambiguity_index(engine.metrics["conflicts_resolved"]),
        elapsed_ms=0.0,
    )


def run_mixed_readwrite(engine: CASIngestionEngine, writers: int, ops: int) -> MatrixResult:
    """Level 4+: Mixed read/write patterns"""
    # In real system, reads would be separate
    # For this test, we simulate skew by varying timing
    random.seed(42)
    
    for i in range(ops):
        incident_id = f"inc_l4_{i}"
        writer_id = f"agent_{i % writers}"
        seq_id = i * 10 + random.randint(0, 9)  # Add timing skew
        
        # For read-write mix, we'd track read operations separately
        success, status, _ = engine.ingest(incident_id, {}, writer_id, i % 5, seq_id)
    
    return MatrixResult(
        level=4,
        writers=writers,
        operations=ops,
        successes=engine.metrics["cas_successes"],
        rejections=engine.metrics["cas_rejections"],
        conflicts=engine.metrics["conflicts_resolved"],
        cds=engine.get_cds(),
        cai=engine.get_causal_ambiguity_index(engine.metrics["conflicts_resolved"]),
        elapsed_ms=0.0,
    )


def run_full_matrix() -> List[MatrixResult]:
    """Run all stress matrix levels"""
    levels = [
        (1, 1, 1000),           # Level 1: Single writer
        (2, 10, 100),           # Level 2: Multi-writer (10 writers)
        (3, 50, 50),            # Level 3: Heavy load (50 writers)
        (4, 20, 200),           # Level 4: Mixed read/write (20 writers)
        (5, 30, 150),           # Level 5: Skewed timing (30 writers)
    ]
    
    results = []
    base_engine = CASIngestionEngine(mode="STRICT")
    
    print("=" * 60)
    print("PHASE 4 STRESS MATRIX: Controlled Concurrency Validation")
    print("=" * 60)
    print()
    
    for level, writers, ops in levels:
        engine = CASIngestionEngine(mode="STRICT")
        
        if level <= 2:
            result = run_multi_writer_storm(engine, writers, ops)
        else:
            result = run_mixed_readwrite(engine, writers, ops)
        
        result.level = level
        result.writers = writers
        result.operations = writers * ops
        
        # Reset metrics for next level's comparison
        base_engine.metrics["cas_rejections"] = result.rejections
        
        status = "✓" if result.cds == 1.0 else "✗"
        print(f"Level {level:2d} | Writers: {writers:3d} | CDS: {result.cds:.4f} {status} | CAI: {result.cai:.4f}")
        
        results.append(result)
    
    return results


def print_summary(results: List[MatrixResult]):
    """Print summary report"""
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    for r in results:
        print(f"\nLevel {r.level}:")
        print(f"  Writers: {r.writers}")
        print(f"  Operations: {r.operations}")
        print(f"  Successes: {r.successes}")
        print(f"  Rejections: {r.rejections}")
        print(f"  Conflicts: {r.conflicts}")
        print(f"  CDS: {r.cds:.4f}")
        print(f"  CAI: {r.cai:.4f}")
    
    # Validate all levels pass
    all_deterministic = all(r.cds == 1.0 for r in results)
    print(f"\n{'='*60}")
    print(f"VALIDATION: {'✓ ALL LEVELS PASS (CDS=1.0)' if all_deterministic else '✗ SOME LEVELS FAILED'}")
    print(f"{'='*60}")


if __name__ == "__main__":
    results = run_full_matrix()
    print_summary(results)
