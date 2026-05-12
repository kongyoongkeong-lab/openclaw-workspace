#!/usr/bin/env python3
"""
Test concurrent failure signals to verify orchestrator conflict resolution.
"""

import sys
import time
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace")
from self_repair_orchestrator import register_failure, get_health


def simulate_concurrent_failures():
    print("🧪 SIMULATING CONCURRENT FAILURES...")
    print("-" * 60)
    
    # Initialize orchestrator fresh
    import self_repair_orchestrator as sr
    sr._orchestrator = sr.RepairOrchestrator()  # Reset singleton
    
    # Simulate failures in priority order (CRITICAL first)
    # This tests: will orchestrator select highest priority action?
    failures = [
        ("workspace", "Corrupted file: data/episodes/12345.jsonl"),  # CRITICAL
    ]
    
    # Register first critical failure
    register_failure(failures[0][0], failures[0][1])
    time.sleep(0.3)
    
    print("\n1️⃣ First critical signal registered")
    health = get_health()
    print(f"   Active signals: {health['active_signals_count']}")
    
    # Wait for cooldown
    time.sleep(0.05)
    
    # Now add a HIGH priority signal (should be queued, not execute)
    register_failure("timeout", "Agent timeout storm: 12 agents exceeded T=30s")
    time.sleep(0.3)
    
    health = get_health()
    print("\n2️⃣ Added HIGH priority signal (should be queued)")
    print(f"   Active signals: {health['active_signals_count']}")
    print(f"   Queued actions: {health['queued_actions_count']}")


if __name__ == "__main__":
    simulate_concurrent_failures()
