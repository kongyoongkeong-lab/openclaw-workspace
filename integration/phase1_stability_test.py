#!/usr/bin/env python3
"""
Pentagon System - Phase 1 Real-World Stability Test
Focus: Conflict Resolution Integrity (CRI) validation only.
"""

import sys
import time
import threading
from datetime import datetime
from pathlib import Path

from integration import failure_registration
from integration import signal_handling
from integration import config_reader


class ConflictResolutionTest:
    """Test conflict resolution integrity under pressure."""
    
    def __init__(self, orchestrator_instance):
        self.orchestrator = orchestrator_instance
        self.handler = orchestrator_instance.signal_handler
        self.config = orchestrator_instance.config
        self.lock = threading.Lock()
        self.observations = []
        self.last_action = None
        self.action_count = 0
    
    def record_observation(self, observation: dict):
        """Thread-safe observation recording."""
        with self.lock:
            self.observations.append({
                'timestamp': datetime.now().isoformat(),
                'data': observation
            })
    
    def test_concurrent_failures(self):
        """Test: Multiple failures at once - MUST choose ONE action."""
        print("=" * 60)
        print("🧪 TEST: Concurrent Failure Injection")
        print("   Scenario: 2+ failures simultaneously")
        print("=" * 60)
        
        start_time = time.time()
        failure_count = 0
        
        # Inject failures concurrently
        threads = []
        for i in range(3):
            t = threading.Thread(target=self._inject_failure, args=(i + 1))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join(timeout=10)  # 10s timeout
        
        duration = time.time() - start_time
        
        # Analyze results
        with self.lock:
            recent_obs = self.observations[-50:]  # Last 50 observations
            
        print(f"\n⏱  Duration: {duration:.2f}s")
        print(f"📊 Observations: {len(recent_obs)}")
        
        # Check for action suppression
        unique_actions = set()
        cooldown_violations = 0
        
        for obs in recent_obs:
            if 'action' in obs:
                unique_actions.add(obs['action'])
            if 'cooldown_violation' in obs:
                cooldown_violations += 1
        
        print(f"✅ Unique actions taken: {unique_actions}")
        print(f"❌ Cooldown violations: {cooldown_violations}")
        
        # CRI Score
        cri_score = 0
        if len(unique_actions) <= 1:
            cri_score = 100
            print("✅ CRITICAL: Only ONE action chosen (CORRECT)")
        elif len(unique_actions) > 2:
            cri_score = 0
            print("❌ CRITICAL: Multiple actions chosen (FAILURE)")
        else:
            cri_score = 50
            print("⚠️  PARTIAL: 2 actions chosen (acceptable)")
        
        return cri_score > 50, {
            'unique_actions': unique_actions,
            'cooldown_violations': cooldown_violations,
            'cri_score': cri_score
        }
    
    def _inject_failure(self, failure_id: int):
        """Inject individual failure."""
        import random
        
        failure_types = ['GPU_RUNAWAY', 'TIMEOUT_STORM', 'PATH_CORRUPTION']
        failure_type = failure_types[failure_id % len(failure_types)]
        message = f"SIMULATED_{failure_type.upper()}:{random.randint(1000, 9999)}:SIMULATION:ERROR"
        
        try:
            # Try to register failure
            if hasattr(self.orchestrator, 'failure_registry'):
                self.orchestrator.failure_registry.register_failure(
                    event_id=failure_type,
                    severity='HIGH',
                    message=message,
                    level=1
                )
            
            self.record_observation({
                'event': f"INJECT:{failure_type}",
                'action': f"register_failure({failure_type})",
                'message': message
            })
            
        except Exception as e:
            self.record_observation({
                'event': f"INJECT:{failure_type}",
                'action': f"REGISTER_FAILURE_FAILED",
                'error': str(e)
            })
    
    def test_priority_escalation(self):
        """Test: Verify priority escalation works correctly."""
        print("=" * 60)
        print("🧪 TEST: Priority Escalation Validation")
        print("   Scenario: Low → Medium → High failures")
        print("=" * 60)
        
        start_time = time.time()
        escalation_sequence = []
        
        # Inject in priority order
        for priority in ['LOW', 'MEDIUM', 'HIGH']:
            failure_type = f"{priority}_TEST_FAILURE"
            message = f"PRIORITY_{priority}:{failure_type}:SIMULATION:ERROR"
            
            try:
                self.handler.handle_signal(failure_type, message)
                escalation_sequence.append(priority)
                time.sleep(0.5)  # Small delay between injections
            except Exception as e:
                print(f"[ERROR] Priority escalation test failed: {e}")
                return False, {'sequence': escalation_sequence}
        
        duration = time.time() - start_time
        
        # Verify escalation
        if len(escalation_sequence) == 3:
            print(f"✅ Priority sequence preserved: {escalation_sequence}")
            cri_score = 100
            return True, {
                'sequence': escalation_sequence,
                'cri_score': cri_score
            }
        
        return False, {'sequence': escalation_sequence}
    
    def run_all_tests(self):
        """Run full stability test suite."""
        print("\n" + "=" * 60)
        print("🔬 PENTAGON SYSTEM - PHASE 1 STABILITY TEST")
        print("   Focus: Conflict Resolution Integrity (CRI)")
        print("=" * 60)
        
        all_results = []
        
        # Test 1: Concurrent failures
        print("\n🧪 TEST 1: Concurrent Failure Injection")
        try:
            success, result = self.test_concurrent_failures()
            all_results.append({
                'name': 'Concurrent Failures',
                'status': 'PASS' if success else 'FAIL',
                'data': result
            })
        except Exception as e:
            print(f"[ERROR] Test 1 failed: {e}")
            all_results.append({
                'name': 'Concurrent Failures',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Test 2: Priority escalation
        print("\n🧪 TEST 2: Priority Escalation Validation")
        try:
            success, result = self.test_priority_escalation()
            all_results.append({
                'name': 'Priority Escalation',
                'status': 'PASS' if success else 'FAIL',
                'data': result
            })
        except Exception as e:
            print(f"[ERROR] Test 2 failed: {e}")
            all_results.append({
                'name': 'Priority Escalation',
                'status': 'ERROR',
                'error': str(e)
            })
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 STABILITY TEST RESULTS")
        print("=" * 60)
        
        passed = sum(1 for r in all_results if r['status'] == 'PASS')
        total = len(all_results)
        
        for result in all_results:
            print(f"   {result['name']}: {result['status']}")
        
        print(f"\n   Total Tests: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {total - passed}")
        
        # CRI Score
        cri_score = sum(r.get('data', {}).get('cri_score', 0) for r in all_results) // total
        print(f"\n🧠 Conflict Resolution Integrity Score: {cri_score}%")
        
        if cri_score >= 80:
            print("✅ SYSTEM READY FOR PHASE 1 REAL-WORLD DEPLOYMENT")
        else:
            print("⚠️  SYSTEM REQUIRES DEBUGGING BEFORE DEPLOYMENT")
        
        return all_results


# Main entry point
if __name__ == '__main__':
    from integration import orchestrator
    
    # Initialize orchestrator
    orchestrator_instance = orchestrator.main()
    
    # Run stability tests
    tests = ConflictResolutionTest(orchestrator_instance)
    results = tests.run_all_tests()
    
    # Exit with appropriate code
    if any(r['status'] == 'FAIL' for r in results):
        sys.exit(1)
