#!/usr/bin/env python3
"""
Self-Repair Effectiveness Test Suite
Triggers controlled failures and measures recovery metrics
"""

import time
import random
import json
from datetime import datetime
from pathlib import Path

class RepairMetrics:
    def __init__(self):
        self.mtt = []
        self.attempts = []
        self.loops = 0
        self.recovery_quality = []
        
    def record_failure(self):
        self.failure_time = time.time()
        
    def record_success(self, duration):
        self.mtt.append(duration)
        self.recovery_quality.append("success")
        return duration
        
    def record_retry(self):
        self.attempts.append(len(self.attempts) + 1)
        
    def check_loop(self):
        self.loops += 1
        
    def get_stats(self):
        if not self.mtt:
            return {"mttr": 0, "avg_mtt": 0, "std": 0}
        avg = sum(self.mtt) / len(self.mtt)
        variance = sum((x - avg) ** 2 for x in self.mtt) / len(self.mtt)
        return {
            "mttr": self.mtt[-1] if self.mtt else 0,
            "avg_mtt": avg,
            "std": variance ** 0.5,
            "total_failures": len(self.mtt),
            "total_attempts": sum(self.attempts),
            "loops": self.loops
        }

class ControlledFailure:
    """Simulates various failure modes"""
    
    def __init__(self, failure_type="network"):
        self.failure_type = failure_type
        self.is_failing = False
        
    def trigger_failure(self):
        self.is_failing = True
        return {
            "type": self.failure_type,
            "timestamp": datetime.now().isoformat(),
            "status": "FAILED"
        }
        
    def is_failing(self):
        return self.is_failing
        
    def simulate_failure(self):
        """Simulate failure based on type"""
        failures = {
            "network": lambda: random.randint(100, 5000),  # Network latency/jitter
            "memory": lambda: random.randint(500, 10000),   # Memory pressure
            "disk": lambda: random.randint(200, 8000),      # I/O bottleneck
            "compute": lambda: random.randint(300, 12000)   # GPU/CPU overload
        }
        
        if self.failure_type in failures:
            return failures[self.failure_type]()
        return random.randint(100, 5000)

class RepairStrategy:
    """Implements repair strategies"""
    
    def __init__(self, metrics: RepairMetrics):
        self.metrics = metrics
        self.strategy = "linear"  # linear, exponential, exponential_backoff
        self.max_retries = 5
        self.base_delay = 1.0
        
    def repair(self, failure_duration):
        """Attempt repair, returns duration until success"""
        start = time.time()
        
        for attempt in range(self.max_retries):
            # Simulate repair time (shorter on retries)
            repair_time = failure_duration / (2 ** attempt) if attempt > 0 else failure_duration
            time.sleep(min(repair_time, 0.1))  # Cap at 100ms for testing
            
            # Check if repair succeeded
            success = random.random() > 0.2  # 80% success rate
            
            if success:
                duration = time.time() - start
                self.metrics.record_success(duration)
                self.metrics.record_retry()
                return duration
            
            # Check for repair loop
            if attempt > 2:
                self.metrics.check_loop()
                
        # Failed all retries
        self.metrics.check_loop()
        return 0

def run_self_repair_test(failure_types=["network", "memory", "disk", "compute"]):
    """Run comprehensive self-repair effectiveness test"""
    
    print("=" * 60)
    print("🧪 SELF-REPAIR EFFECTIVENESS TEST SUITE")
    print("=" * 60)
    
    metrics = RepairMetrics()
    all_stats = {}
    
    for failure_type in failure_types:
        print(f"\n📟 Testing failure type: {failure_type.upper()}")
        print("-" * 40)
        
        failure = ControlledFailure(failure_type)
        strategy = RepairStrategy(metrics)
        
        # Run multiple trials for statistical significance
        trials = 10
        for trial in range(trials):
            print(f"  Trial {trial + 1}/{trials}")
            
            # Trigger failure
            failure_result = failure.trigger_failure()
            print(f"    📌 Failure triggered: {failure_result['status']}")
            
            # Attempt repair
            duration = strategy.repair(failure.simulate_failure())
            
            if duration > 0:
                print(f"    ✅ Recovered in {duration:.2f}s")
            else:
                print(f"    ❌ Recovery failed after {strategy.max_retries} retries")
    
    # Print final statistics
    stats = metrics.get_stats()
    
    print("\n" + "=" * 60)
    print("📊 RECOVERY METRICS SUMMARY")
    print("=" * 60)
    
    print(f"📌 Total Failures: {stats['total_failures']}")
    print(f"⏱️  MTTR (Last): {stats['mttr']:.2f}s")
    print(f"📉 Average MTTR: {stats['avg_mtt']:.2f}s")
    print(f"🔄 Standard Deviation: {stats['std']:.2f}s")
    print(f"📋 Total Attempts: {stats['total_attempts']}")
    print(f"🔄 Detected Loops: {stats['loops']}")
    
    # Auto-Improvement Analysis
    print("\n" + "=" * 60)
    print("🧠 AUTO-IMPROVEMENT ANALYSIS")
    print("=" * 60)
    
    issues = []
    
    # Check MTTR threshold
    if stats['avg_mtt'] > 5.0:
        issues.append(f"⚠️  MTTR ({stats['avg_mtt']:.2f}s) exceeds 5s threshold")
        issues.append("💡 SUGGESTION: Implement staged recovery escalation")
    
    # Check for repeated retries
    if stats['total_attempts'] > stats['total_failures'] * 3:
        issues.append(f"⚠️  High retry ratio: {stats['total_attempts']}/{stats['total_failures']}")
        issues.append("💡 SUGGESTION: Add retry ceilings per failure type")
    
    # Check for repair loops
    if stats['loops'] > 3:
        issues.append(f"⚠️  Repair loops detected: {stats['loops']}")
        issues.append("💡 SUGGESTION: Implement progressive degradation modes")
    
    # Check aggressiveness
    if stats['avg_mtt'] > 10.0:
        issues.append("⚠️  Recovery time indicates overly aggressive repairs")
        issues.append("💡 SUGGESTION: Reduce repair aggressiveness")
    
    if issues:
        print("\n🚨 ISSUES DETECTED:")
        for issue in issues:
            print(f"  {issue}")
            
        print("\n📋 RECOMMENDED IMPROVEMENTS:")
        print("  1. Implement staged recovery escalation:")
        print("     - Level 1: Quick retry (0.1s)")
        print("     - Level 2: Circuit breaker pattern")
        print("     - Level 3: Progressive degradation")
        print("     - Level 4: Full restart with isolation")
        print("\n  2. Add retry ceilings:")
        print("     - Network failures: max 5 retries")
        print("     - Memory issues: max 3 retries")
        print("     - Disk issues: max 4 retries")
        print("     - Compute issues: max 2 retries")
        print("\n  3. Implement progressive degradation:")
        print("     - Fallback to cache")
        print("     - Reduce batch sizes")
        print("     - Throttle request rate")
        print("\n  4. Reduce repair aggressiveness:")
        print("     - Add exponential backoff")
        print("     - Implement circuit breakers")
        print("     - Add health checks before full recovery")
    else:
        print("\n✅ System performing within normal parameters")
    
    return stats

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        failure_type = sys.argv[1]
        if failure_type in ["network", "memory", "disk", "compute"]:
            run_self_repair_test([failure_type])
        else:
            print(f"Unknown failure type: {failure_type}")
            run_self_repair_test()
    else:
        run_self_repair_test()
