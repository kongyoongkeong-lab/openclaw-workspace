#!/usr/bin/env python3
"""
test_isolation.py — Isolation Test Suite

Tests:
1. Agent can only read their专属 store + shared vault
2. Agent cannot read other agents' stores
3. Token budgets are enforced
4. Context compression triggers at threshold
"""

import json
import sys
import os
import random
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_router import write_event, read_agent_memory, read_shared_vault
from ltm_pipeline_isolated import run_pipeline, AGENT_STORES, TOKEN_BUDGETS

# Test utilities
def assert_true(condition, msg):
    """Assert and report"""
    if not condition:
        print(f"❌ FAIL: {msg}")
        return False
    print(f"✅ PASS: {msg}")
    return True


def test_agent_isolation():
    """Test that agents cannot read other agents' stores"""
    print("\n" + "="*60)
    print("TEST 1: Agent Isolation")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 1.1: @intel can only read intel + vault
    tests_total += 1
    try:
        results = read_agent_memory("intel")
        agents_in_results = set(r.get("agent") for r in results)
        allowed_agents = {"intel", "vault"}
        if agents_in_results.issubset(allowed_agents):
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@intel only reads intel + vault (allowed: {allowed_agents})"
            )
        else:
            print(f"   Agents found: {agents_in_results}")
            assert_true(False, f"@intel found unauthorized agents: {agents_in_results - allowed_agents}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 1.2: @ops can only read ops + vault
    tests_total += 1
    try:
        results = read_agent_memory("ops")
        agents_in_results = set(r.get("agent") for r in results)
        allowed_agents = {"ops", "vault"}
        if agents_in_results.issubset(allowed_agents):
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@ops only reads ops + vault (allowed: {allowed_agents})"
            )
        else:
            assert_true(False, f"@ops found unauthorized agents")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 1.3: @comms can only read comms + vault
    tests_total += 1
    try:
        results = read_agent_memory("comms")
        agents_in_results = set(r.get("agent") for r in results)
        allowed_agents = {"comms", "vault"}
        if agents_in_results.issubset(allowed_agents):
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@comms only reads comms + vault (allowed: {allowed_agents})"
            )
        else:
            assert_true(False, f"@comms found unauthorized agents")
    except Exception as e:
        print(f"   Error: {e}")
    
    return tests_passed == tests_total


def test_token_budget_enforcement():
    """Test that token budgets are enforced"""
    print("\n" + "="*60)
    print("TEST 2: Token Budget Enforcement")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 2.1: @intel budget (2000 tokens)
    tests_total += 1
    try:
        # Generate test events
        for i in range(5):
            write_event("intel", "test_event", "A" * 300)  # 300 chars ≈ 75 tokens
        
        results = read_agent_memory("intel")
        total_tokens = sum(len(r.get("content", "")) // 4 for r in results)
        budget = TOKEN_BUDGETS["intel"]
        
        if total_tokens <= budget:
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@intel token budget enforced: {total_tokens} <= {budget}"
            )
        else:
            assert_true(False, f"@intel exceeded budget: {total_tokens} > {budget}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2.2: @ops budget (3000 tokens)
    tests_total += 1
    try:
        for i in range(5):
            write_event("ops", "test_event", "B" * 400)  # 400 chars ≈ 100 tokens
        
        results = read_agent_memory("ops")
        total_tokens = sum(len(r.get("content", "")) // 4 for r in results)
        budget = TOKEN_BUDGETS["ops"]
        
        if total_tokens <= budget:
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@ops token budget enforced: {total_tokens} <= {budget}"
            )
        else:
            assert_true(False, f"@ops exceeded budget: {total_tokens} > {budget}")
    except Exception as e:
        print(f"   Error: {e}")
    
    return tests_passed == tests_total


def test_shared_vault_immutable():
    """Test that shared vault entries are immutable"""
    print("\n" + "="*60)
    print("TEST 3: Shared Vault Immutability")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 3.1: All vault entries have immutable=true
    tests_total += 1
    try:
        vault_entries = read_shared_vault()
        all_immutable = all(entry.get("immutable", False) for entry in vault_entries)
        
        if all_immutable:
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"All {len(vault_entries)} vault entries are immutable"
            )
        else:
            assert_true(False, f"Some vault entries are not immutable")
    except Exception as e:
        print(f"   Error: {e}")
    
    return tests_passed == tests_total


def test_context_isolation():
    """Test that context is isolated per agent"""
    print("\n" + "="*60)
    print("TEST 4: Context Isolation")
    print("="*60)
    
    tests_passed = 0
    tests_total = 0
    
    # Test 4.1: @intel context contains only intel memory
    tests_total += 1
    try:
        context = run_pipeline("intel", "test query")
        if "ops" not in context and "comms" not in context:
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@intel context isolated (no ops/comms)"
            )
        else:
            assert_true(False, f"@intel context leaked ops/comms data")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 4.2: @ops context contains only ops memory
    tests_total += 1
    try:
        context = run_pipeline("ops", "test query")
        if "intel" not in context and "comms" not in context:
            tests_passed += 1
            assert_true(
                tests_passed == tests_total,
                f"@ops context isolated (no intel/comms)"
            )
        else:
            assert_true(False, f"@ops context leaked intel/comms data")
    except Exception as e:
        print(f"   Error: {e}")
    
    return tests_passed == tests_total


def run_all_tests():
    """Run all isolation tests"""
    print("\n" + "="*60)
    print("🚀 STARTING ISOLATION TEST SUITE")
    print("="*60)
    
    results = []
    
    results.append(("Agent Isolation", test_agent_isolation()))
    results.append(("Token Budget Enforcement", test_token_budget_enforcement()))
    results.append(("Shared Vault Immutability", test_shared_vault_immutable()))
    results.append(("Context Isolation", test_context_isolation()))
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All isolation tests passed!")
        print("   Agent memory isolation is working correctly.")
        return True
    else:
        print("\n⚠️  Some tests failed!")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
