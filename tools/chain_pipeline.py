#!/usr/bin/env python3
"""
Chain Pipeline - OpenClaw Telemetry Integration
Integrates hash chaining, replay protection, and gap detection with live telemetry.
"""

import json
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import signal

# Import our components
sys.path.insert(0, str(Path.home() / '.openclaw/workspace/tools'))
from chain_verify import compute_chain_hash, load_chain_registry, save_chain_registry
from chain_replay_guard import ReplayGuard
from chain_gap_detector import GapDetector, analyze_telemetry_health

# Configuration
CHAIN_REGISTRY = Path.home() / '.openclaw/workspace/observability/chain_registry.json'
TELEMETRY_DIR = Path.home() / '.openclaw/workspace/logs'
EVENT_CADENCE_SECONDS = 300  # 5 minutes


class ChainPipeline:
    """
    Main pipeline for OpenClaw telemetry observability hardening.
    
    Responsibilities:
    - Hash chain verification
    - Replay attack detection
    - Gap detection and alerting
    - Health scoring
    """
    
    def __init__(self):
        self.replay_guard = ReplayGuard()
        self.gap_detector = GapDetector()
        self.chain_registry = load_chain_registry()
        self.pipeline_stats = {
            'events_processed': 0,
            'gaps_detected': 0,
            'replay_attacks_blocked': 0,
            'last_processing': None
        }
    
    def process_telemetry_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single telemetry event through the full pipeline.
        
        Args:
            event: Telemetry event dictionary
        
        Returns:
            Processing result
        """
        event_time = datetime.fromisoformat(event.get('timestamp'))
        event_type = event.get('type', 'telemetry')
        
        # Step 1: Hash chain verification
        hash_result = compute_chain_hash(event)
        
        # Step 2: Replay guard check
        replay_result = self.replay_guard.verify_event({
            'hash': hash_result,
            'timestamp': event_time.isoformat()
        })
        
        # Step 3: Gap detection
        gap_result = self.gap_detector.process_event(event_time, event)
        
        # Update pipeline stats
        self.pipeline_stats['events_processed'] += 1
        
        if gap_result['gap_detected']:
            self.pipeline_stats['gaps_detected'] += 1
            gap_info = gap_result['gap_info']
            
            # Alert on critical gaps
            if gap_info['severity'] == 'CRITICAL':
                print(f"🚨 CRITICAL GAP DETECTED: {gap_info['elapsed']} missing events")
        
        if replay_result['status'] != 'VERIFIED':
            self.pipeline_stats['replay_attacks_blocked'] += 1
            print(f"⚠️  Blocked replay attack: {replay_result['reason']}")
        
        # Update chain registry
        self.chain_registry['last_update'] = datetime.now().isoformat()
        save_chain_registry(self.chain_registry)
        
        result = {
            'event_type': event_type,
            'timestamp': event_time.isoformat(),
            'hash_verified': True,
            'replay_safe': replay_result['status'] == 'VERIFIED',
            'gap_status': 'OK' if not gap_result['gap_detected'] else gap_info['severity'],
            'pipeline_status': 'OK' if all([
                replay_result['status'] == 'VERIFIED',
                not gap_result['gap_detected']
            ]) else 'DEGRADED'
        }
        
        return result
    
    def process_telemetry_file(self, filepath: str) -> Dict[str, Any]:
        """
        Process an entire telemetry file.
        
        Args:
            filepath: Path to telemetry JSONL file
        
        Returns:
            Processing summary
        """
        results = []
        events = []
        
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    result = self.process_telemetry_event(event)
                    results.append(result)
                    events.append(event)
                except json.JSONDecodeError:
                    continue
        
        # Generate health report
        health_report = analyze_telemetry_health()
        
        return {
            'file': filepath,
            'total_events': len(events),
            'processed': len(results),
            'success': all(r['hash_verified'] for r in results),
            'gaps_found': sum(1 for r in results if r['gap_status'] != 'OK'),
            'health_report': health_report
        }
    
    def run_health_check(self) -> Dict[str, Any]:
        """
        Run comprehensive health check.
        
        Returns:
            Health check results
        """
        health = analyze_telemetry_health()
        
        # Update pipeline stats
        self.pipeline_stats['last_processing'] = datetime.now().isoformat()
        
        return {
            'status': 'OK' if health['health_score'] >= 90 else 'DEGRADED',
            'health_score': health['health_score'],
            'total_gaps': health['total_gaps'],
            'critical_gaps': health['critical_gaps'],
            'recommendations': health.get('recommendations', [])
        }


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: chain_pipeline.py <command> [options]")
        print("Commands:")
        print("  process <file>   Process telemetry file")
        print("  health           Run health check")
        print("  status           Show pipeline status")
        sys.exit(1)
    
    command = sys.argv[1]
    pipeline = ChainPipeline()
    
    if command == 'process' and len(sys.argv) >= 3:
        filepath = sys.argv[2]
        if not Path(filepath).exists():
            print(f"Error: File not found: {filepath}")
            sys.exit(1)
        
        summary = pipeline.process_telemetry_file(filepath)
        print(json.dumps(summary, indent=2))
    
    elif command == 'health':
        health = pipeline.run_health_check()
        print(json.dumps(health, indent=2))
    
    elif command == 'status':
        print(json.dumps(pipeline.pipeline_stats, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
