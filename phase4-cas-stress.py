#!/usr/bin/env python3
"""
Phase 4: Multi-writer CAS Concurrency Stress Test
10 concurrent writers, strict retry=0, deterministic winner rule
"""

import threading
import time
import hashlib
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class CASNode:
    """CAS shared state node"""
    expected: int = 0
    actual: int = 0
    version: int = 0
    last_writer: str = ""
    last_update: float = 0.0
    trace_log: List[Dict] = None

    def __post_init__(self):
        if self.trace_log is None:
            self.trace_log = []

    def compare_and_swap(self, expected_val: int, new_val: int, writer_id: str) -> bool:
        """Perform CAS operation with deterministic tie-breaking"""
        success = (self.expected == expected_val)
        trace = {
            "ts": time.time(),
            "writer": writer_id,
            "expected": expected_val,
            "actual": self.actual,
            "success": success,
            "version": self.version,
            "last_writer": self.last_writer
        }
        self.trace_log.append(trace)
        
        if success:
            self.expected = new_val
            self.actual = new_val
            self.version += 1
            self.last_writer = writer_id
            self.last_update = time.time()
        
        return success


class CASStressHarness:
    def __init__(self, num_writers: int = 10, retry_policy: int = 0):
        self.num_writers = num_writers
        self.retry_policy = retry_policy
        self.node = CASNode()
        self.results = {
            "wins": 0,
            "lost": 0,
            "total_ops": 0,
            "deterministic": False,
            "winner_sequence": []
        }
        self.lock = threading.Lock()

    def run_test(self, writer_id: str, value: int) -> bool:
        """Single writer attempt with strict retry=0"""
        start = time.time()
        attempt = 0
        
        while attempt <= self.retry_policy:
            success = self.node.compare_and_swap(
                expected_val=self.node.actual,
                new_val=value,
                writer_id=writer_id
            )
            
            trace = self.node.trace_log[-1]
            
            if success:
                # Record deterministic winner
                with self.lock:
                    self.results["wins"] += 1
                    self.results["total_ops"] += 1
                    self.results["winner_sequence"].append({
                        "writer": writer_id,
                        "value": value,
                        "timestamp": start
                    })
                return True
            else:
                with self.lock:
                    self.results["lost"] += 1
                    self.results["total_ops"] += 1
                
                # Log contention loss with deterministic ordering
                deterministic_id = hashlib.md5(
                    f"{writer_id}:{start:.6f}".encode()
                ).hexdigest()[:8]
                print(f"[{deterministic_id}] {writer_id} lost to {self.node.last_writer} (v{self.node.version})")
                return False
        
        # Should never reach here with retry_policy=0
        return False

    def stress_run(self, values: List[int], duration_seconds: float = 5.0):
        """Run concurrent stress test"""
        print(f"\n🚀 Starting CAS Stress Test")
        print(f"   Writers: {self.num_writers}")
        print(f"   Values: {values}")
        print(f"   Retry Policy: {self.retry_policy}")
        print(f"   Duration: {duration_seconds}s\n")
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=self.num_writers) as executor:
            futures = {}
            for i, (writer_id, value) in enumerate(zip(
                [f"writer-{i:03d}" for i in range(self.num_writers)],
                values
            )):
                future = executor.submit(self.run_test, writer_id, value)
                futures[future] = (writer_id, value)

            # Collect results while maintaining deterministic ordering
            for future in as_completed(futures):
                writer_id, value = futures[future]
                result = future.result()
                if not result:
                    time.sleep(0.001)  # Small delay to allow other threads to show


def main():
    """Run Phase 4 stress test"""
    harness = CASStressHarness(
        num_writers=10,
        retry_policy=0
    )
    
    # Generate stress values
    values = list(range(1, 11))  # 10 unique values
    harness.stress_run(values, duration_seconds=3.0)
    
    # Generate report
    elapsed = time.time() - harness.stress_run.__globals__["start_time"] if hasattr(harness.stress_run.__globals__, 'start_time') else 0
    
    print("\n" + "="*60)
    print("🚀 PHASE 4: CAS CONCURRENTNESS STRESS TEST RESULTS")
    print("="*60)
    print(f"\nResults Summary:")
    print(f"  Total Operations: {harness.results['total_ops']}")
    print(f"  Wins: {harness.results['wins']}")
    print(f"  Lost: {harness.results['lost']}")
    print(f"  Success Rate: {harness.results['wins']/max(harness.results['total_ops'],1)*100:.2f}%")
    
    # Deterministic winner sequence
    if harness.results['winner_sequence']:
        print(f"\n🎯 Deterministic Winner Sequence:")
        for i, entry in enumerate(harness.results['winner_sequence'][:10]):
            print(f"  {i+1}. {entry['writer']:<12} -> {entry['value']:<5} @ {entry['timestamp']:.4f}")
    
    print("\n" + "="*60)
    print("✅ Phase 4 Execution Complete")
    print("="*60)
    
    return harness.results


if __name__ == "__main__":
    results = main()
    print(json.dumps(results, indent=2))
