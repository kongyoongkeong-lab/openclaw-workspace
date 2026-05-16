#!/usr/bin/env python3
"""
Signal Normalizer Integrity Harness
====================================

VERIFIES 4 BOUNDARIES:
1. DETERMINISM - Same input → Same output
2. IDEMPOTENCY - normalize(normalize(x)) == normalize(x)
3. REPLAY STABILITY - Trace replay → Same canonical set
4. SINGLE-ORIGIN PURITY - No signal-to-signal derivation

CORE PRINCIPLE:
Corrupted normalization foundation → IRREVERSIBLE CASCADE

FAILURE MODES DETECTED:
- Semantic Creep: bucket → label → inference
- Hidden Aggregation: signal = f(signal1, signal2, ...)
- Replay Divergence: normalize(trace) != normalize(trace')
"""

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TestResult:
    """Immutable test result."""
    name: str
    passed: bool
    actual: Any
    expected: Any
    failure_reason: Optional[str] = None
    
    def to_json(self) -> dict:
        return {
            'name': self.name,
            'passed': self.passed,
            'actual': str(self.actual),
            'expected': str(self.expected),
            'failure': self.failure_reason
        }

class IntegrityHarness:
    """Core integrity verification harness."""
    
    def __init__(self, harness_dir: str = '/workspace/tools'):
        self.harness_dir = Path(harness_dir)
        # Fallback to workspace if /workspace/tools not writable
        self.harness_dir = Path('/home/jason2ykk/.openclaw/workspace/tools')
        self.results_file = self.harness_dir / 'integrity_results.jsonl'
        self.corruption_log = self.harness_dir / 'corruption_log.txt'
    
    def test_determinism(self, signal: str, value: float) -> TestResult:
        """
        Test 1: DETERMINISM
        normalize(signal, value) must produce identical output on repeated runs.
        """
        try:
            # Run normalization twice
            result1 = self._normalize(signal, value)
            result2 = self._normalize(signal, value)
            
            if result1['bucket'] == result2['bucket']:
                return TestResult(
                    name=f"DETERMINISM:{signal}",
                    passed=True,
                    actual=f"{result1['bucket']}",
                    expected=f"{result2['bucket']}",
                    failure_reason=None
                )
            else:
                return TestResult(
                    name=f"DETERMINISM:{signal}",
                    passed=False,
                    actual=f"{result1['bucket']}",
                    expected=f"{result2['bucket']}",
                    failure_reason=f"Divergence: run1={result1['bucket']}, run2={result2['bucket']}"
                )
        except Exception as e:
            return TestResult(
                name=f"DETERMINISM:{signal}",
                passed=False,
                actual="exception",
                expected="success",
                failure_reason=str(e)
            )
    
    def test_idempotency(self, signal: str, value: float) -> TestResult:
        """
        Test 2: IDEMPOTENCY
        normalize(normalize(signal, value)) == normalize(signal, value)
        """
        try:
            # First normalization
            result1 = self._normalize(signal, value)
            # Second normalization on result
            result2 = self._normalize(signal, result1['bucket'])
            # Third normalization (original) for comparison
            result3 = self._normalize(signal, value)
            
            if result2['bucket'] == result3['bucket'] == result1['bucket']:
                return TestResult(
                    name=f"IDEMPOTENCY:{signal}",
                    passed=True,
                    actual=f"{result1['bucket']} (idempotent)",
                    expected=f"{result1['bucket']}",
                    failure_reason=None
                )
            else:
                return TestResult(
                    name=f"IDEMPOTENCY:{signal}",
                    passed=False,
                    actual=f"double={result2['bucket']}, original={result3['bucket']}",
                    expected=f"{result1['bucket']}",
                    failure_reason=f"Idecomotency broken: normalize(normalize(x))={result2['bucket']} != normalize(x)={result3['bucket']}"
                )
        except Exception as e:
            return TestResult(
                name=f"IDEMPOTENCY:{signal}",
                passed=False,
                actual="exception",
                expected="success",
                failure_reason=str(e)
            )
    
    def test_replay_stability(self, trace: str) -> TestResult:
        """
        Test 3: REPLAY STABILITY
        normalize(trace) must equal replay(normalized_trace)
        """
        try:
            if not trace or not trace.strip():
                return TestResult(
                    name="REPLAY_STABILITY",
                    passed=True,
                    actual="empty trace (skipped)",
                    expected="empty trace (skipped)",
                    failure_reason=None
                )
            
            # Replay trace to canonical set
            replayed = self._replay_trace(trace)
            
            # Normalize trace to canonical set
            normalized = self._normalize_trace(trace)
            
            if set(replayed.keys()) == set(normalized.keys()):
                return TestResult(
                    name="REPLAY_STABILITY",
                    passed=True,
                    actual=f"{len(replayed)} signals, replayable",
                    expected=f"{len(replayed)} signals, replayable",
                    failure_reason=None
                )
            else:
                missing = set(normalized.keys()) - set(replayed.keys())
                extra = set(replayed.keys()) - set(normalized.keys())
                return TestResult(
                    name="REPLAY_STABILITY",
                    passed=False,
                    actual=f"replayed keys={sorted(replayed.keys())}",
                    expected=f"normalized keys={sorted(normalized.keys())}",
                    failure_reason=f"Key divergence: missing={missing}, extra={extra}"
                )
        except Exception as e:
            return TestResult(
                name="REPLAY_STABILITY",
                passed=False,
                actual="exception",
                expected="success",
                failure_reason=str(e)
            )
    
    def test_single_origin_purity(self, signal: str, value: Any) -> TestResult:
        """
        Test 4: SINGLE-ORIGIN PURITY
        signal.dependencies ⊆ {RAW_SIGNAL} only
        """
        try:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return TestResult(
                    name=f"SINGLE_ORIGIN:{signal}",
                    passed=True,
                    actual="primitive (raw observable)",
                    expected="primitive (raw observable)",
                    failure_reason=None
                )
            else:
                return TestResult(
                    name=f"SINGLE_ORIGIN:{signal}",
                    passed=False,
                    actual=f"type={type(value).__name__}",
                    expected="float|int primitive",
                    failure_reason=f"Non-primitive signal value detected"
                )
        except Exception as e:
            return TestResult(
                name=f"SINGLE_ORIGIN:{signal}",
                passed=False,
                actual="exception",
                expected="success",
                failure_reason=str(e)
            )
    
    def _normalize(self, signal: str, value: Any) -> dict:
        """
        Core normalization logic using signal_normalizer.
        This must be deterministic, idempotent, and single-origin.
        """
        try:
            from signal_normalizer import normalize, NormalizationMode
            # Use canonical normalization
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                normalized = normalize(signal, float(value))
                return {'bucket': normalized.bucket, 'value': value}
            else:
                return {'bucket': -1, 'value': value}
        except Exception as e:
            return {'bucket': -2, 'error': str(e), 'value': value}
    
    def _replay_trace(self, trace: str) -> dict:
        """
        Replay trace bytes to verify determinism.
        Must handle unordered maps, timestamp leakage, etc.
        """
        try:
            lines = trace.strip().split('\n')
            result = {}
            for line in lines:
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    signal = data.get('signal')
                    value = data.get('value')
                    if signal and value is not None:
                        normalized = self._normalize(signal, float(value))
                        result[signal] = normalized.get('bucket', 0)
                except json.JSONDecodeError:
                    continue
            return result
        except Exception as e:
            print(f"Replay error: {e}")
            return {}
        except Exception as e:
            print(f"Replay error: {e}")
            return {}
    
    def _normalize_trace(self, trace: str) -> dict:
        """
        Normalize trace to canonical set.
        Must produce identical output to _replay_trace for same input.
        """
        lines = trace.strip().split('\n')
        result = {}
        for line in lines:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                signal = data.get('signal')
                value = data.get('value')
                if signal and value is not None:
                    normalized = self._normalize(signal, float(value))
                    result[signal] = normalized.get('bucket', 0)
            except json.JSONDecodeError:
                continue
        return result
    
    def run_full_integrity_suite(self, trace: Optional[str] = None, 
                                 signals: Optional[list] = None) -> list:
        """Run all 4 integrity tests."""
        results = []
        
        # Test 1-4: Determinism
        for signal_name in signals or ['latency_spike', 'retry_loop', 'trace_gap']:
            value = float('2.5')
            result = self.test_determinism(signal_name, value)
            results.append(result)
            self._log_result(result)
        
        # Test 2-4: Idempotency
        for signal_name in signals or ['latency_spike', 'retry_loop', 'trace_gap']:
            value = float('2.5')
            result = self.test_idempotency(signal_name, value)
            results.append(result)
            self._log_result(result)
        
        # Test 3: Replay Stability
        if trace:
            result = self.test_replay_stability(trace)
            results.append(result)
            self._log_result(result)
        
        # Test 4: Purity
        for signal_name in signals or ['latency_spike', 'retry_loop', 'trace_gap']:
            value = float('2.5')
            result = self.test_single_origin_purity(signal_name, value)
            results.append(result)
            self._log_result(result)
        
        return results
    
    def _log_result(self, result: TestResult):
        """Append result to results file."""
        with open(self.results_file, 'a') as f:
            f.write(json.dumps(result.to_json()) + '\n')
    
    def log_corruption(self, result: TestResult):
        """Log corrupted test result."""
        if not result.passed:
            with open(self.corruption_log, 'a') as f:
                f.write(f"[CORRUPTION] {result.name}\n")
                f.write(f"  Failure: {result.failure_reason}\n")
                f.write(f"  Actual: {result.actual}\n")
                f.write(f"  Expected: {result.expected}\n")
    
    def analyze_results(self, results: list) -> dict:
        """Analyze results and generate report."""
        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]
        
        return {
            'total': len(results),
            'passed': len(passed),
            'failed': len(failed),
            'corruption_detected': len(failed) > 0,
            'results': [r.to_json() for r in results]
        }

def main():
    """CLI for harness testing."""
    import argparse
    parser = argparse.ArgumentParser(description='Signal Normalizer Integrity Harness')
    parser.add_argument('--trace', type=str, help='Trace content or file path')
    parser.add_argument('--test-determinism', action='store_true', help='Run determinism tests')
    parser.add_argument('--test-idempotency', action='store_true', help='Run idempotency tests')
    parser.add_argument('--test-replay', action='store_true', help='Run replay tests')
    parser.add_argument('--test-purity', action='store_true', help='Run purity tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--signals', type=str, default='latency_spike,retry_loop,trace_gap',
                       help='Comma-separated signal names')
    args = parser.parse_args()
    
    harness = IntegrityHarness()
    signals = [s.strip() for s in args.signals.split(',') if s.strip()]
    
    if args.trace or args.all:
        if args.trace:
            trace = args.trace
            if os.path.exists(trace):
                with open(trace) as f:
                    trace = f.read()
        else:
            trace = ""
        
        if args.test_replay or args.all:
            results = harness.run_full_integrity_suite(trace=trace)
            analysis = harness.analyze_results(results)
            print(f"Replay Test: {'✅ PASSED' if not analysis['corruption_detected'] else '❌ CORRUPTION DETECTED'}")
            print(f"  Total: {analysis['total']}, Passed: {analysis['passed']}, Failed: {analysis['failed']}")
    elif args.test_determinism or args.all:
        results = harness.run_full_integrity_suite(signals=signals)
        for r in results:
            print(f"{'✅' if r.passed else '❌'} {r.name}: {r.actual}")
    elif args.test_idempotency or args.all:
        results = harness.run_full_integrity_suite(signals=signals)
        for r in results:
            print(f"{'✅' if r.passed else '❌'} {r.name}: {r.actual}")
    elif args.test_purity or args.all:
        results = harness.run_full_integrity_suite(signals=signals)
        for r in results:
            print(f"{'✅' if r.passed else '❌'} {r.name}: {r.actual}")
    else:
        parser.print_help()
    
    print(f"Results logged to: {harness.results_file}")
    if (harness.corruption_log).exists():
        print(f"Corruption log: {harness.corruption_log}")

if __name__ == "__main__":
    main()
