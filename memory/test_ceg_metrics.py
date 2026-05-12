#!/usr/bin/env python3
"""
Test suite for CEG Metrics modules.
Run: python3 test_ceg_metrics.py
"""

import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace/memory')

from idle_context_occupancy import run_idle_context_analysis, IDLE_THRESHOLD_WARNING, IDLE_THRESHOLD_CRITICAL
from telemetry_integration import (
    compute_rur, compute_go_percent, run_all_ceg_metrics,
    tier_telemetry
)

print("=" * 60)
print("CEG METRICS TEST SUITE")
print("=" * 60)

# Test 1: RUR Computation
print("\n--- Test 1: Retrieval Usefulness Ratio (RUR) ---")
rur = compute_rur(
    retrieved_ids=["mem_001", "mem_002", "mem_003", "mem_004", "mem_005"],
    reasoning_reference_ids=["mem_001", "mem_003", "mem_005"]
)
print(f"  Total Retrieved: 5")
print(f"  Useful Retrievals: 3")
print(f"  RUR: {rur['rur']} ({rur['ratio']})")
assert 0 <= rur['rur'] <= 1, "RUR out of bounds!"

# Test 2: GO% Computation
print("\n--- Test 2: Governance Overhead % (GO%) ---")
go = compute_go_percent(
    governance_tokens=1000,
    productive_tokens=8000
)
print(f"  Governance Tokens: {go['governance_tokens']}")
print(f"  Productive Tokens: {go['productive_tokens']}")
print(f"  GO%: {go['go_percent']}% ({go['ratio']})")
assert 0 <= go['go_percent'] <= 100, "GO% out of bounds!"

# Test 3: Full Metrics Run
print("\n--- Test 3: Full CEG Metrics ---")
context = {
    "retrieved_ids": ["r1", "r2", "r3", "r4", "r5", "r6", "r7"],
    "reasoning_referenced_ids": ["r1", "r2", "r6", "r7"],
    "governance_tokens": 5000,
    "productive_tokens": 45000
}
metrics = run_all_ceg_metrics(context)
print(f"  RUR: {metrics['rur']['rur']}")
print(f"  GO%: {metrics['go_percent']['go_percent']}%")

# Test 4: Tiering System
print("\n--- Test 4: Telemetry Tiering ---")
now = __import__('datetime').datetime.now(__import__('datetime').timezone.utc).timestamp()
telemetry_entries = [
    ("retrieval", now),
    ("compression", now - 10*60),
    ("repair", now - 30*60),
    ("retrieval", now - 30*60*24),
    ("compression", now - 3*24*60*60),
]
for entry_type, ts in telemetry_entries:
    tier = tier_telemetry(entry_type, ts)
    print(f"  {entry_type}: tier={tier}")

# Test 5: Idle Context Analysis
print("\n--- Test 5: Idle Context Occupancy Detector ---")
# This test runs the actual analysis on current memory
report = run_idle_context_analysis(current_turn=10)
print(f"  Total Slots: {report.total_slots}")
print(f"  Idle Slots: {report.idle_slots} ({report.idle_percent:.1f}%)")
if report.warning_slots:
    print(f"  ⚠️  WARNING slots: {len(report.warning_slots)}")
if report.critical_slots:
    print(f"  🚨 CRITICAL slots: {len(report.critical_slots)}")

print("\n" + "=" * 60)
print("✅ All CEG Metrics Tests Passed!")
print("=" * 60)
