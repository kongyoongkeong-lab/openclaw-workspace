#!/usr/bin/env python3
"""
Replay Guard - Event Sequence Integrity Monitor
Prevents replay attacks and event injection.
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configuration
EVENT_CADENCE = timedelta(minutes=5)  # Expected event interval
ALLOWED_VARIANCE = timedelta(minutes=2)
TELEMETRY_DIR = Path.home() / '.openclaw/workspace/logs'
CHAIN_REGISTRY = Path.home() / '.openclaw/workspace/observability/chain_registry.json'


class ReplayGuard:
    """
    Monitor event sequence for replay attacks.
    
    Detects:
    - Duplicate events (same timestamp + hash)
    - Out-of-order events
    - Gaps exceeding cadence
    - Event injection attempts
    """
    
    def __init__(self, cadence: timedelta = EVENT_CADENCE, 
                 variance: timedelta = ALLOWED_VARIANCE):
        self.cadence = cadence
        self.variance = variance
        self.last_events: Dict[str, str] = {}  # hash -> timestamp
        self.gaps: List[Dict[str, Any]] = []
    
    def verify_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify event integrity and detect replay attacks.
        
        Args:
            event: Event dictionary with 'hash' and 'timestamp'
        
        Returns:
            Verification result
        """
        event_hash = event.get('hash')
        event_time = datetime.fromisoformat(event.get('timestamp'))
        
        # Check for duplicate hash (replay attack)
        if event_hash in self.last_events:
            prev_time = datetime.fromisoformat(self.last_events[event_hash])
            time_diff = abs((event_time - prev_time).total_seconds())
            
            return {
                'status': 'REPLAY_DETECTED',
                'reason': 'Duplicate hash in time window',
                'original_time': self.last_events[event_hash],
                'attack_time': event_time,
                'time_diff_seconds': time_diff
            }
        
        # Check for out-of-order events
        if self.last_events:
            last_time = datetime.fromisoformat(list(self.last_events.values())[-1])
            if event_time < last_time:
                return {
                    'status': 'OUT_OF_ORDER',
                    'reason': 'Event timestamp precedes previous event',
                    'expected_min': last_time + self.cadence,
                    'actual': event_time
                }
        
        # Update last events
        self.last_events[event_hash] = event_time
        self.gaps.append({
            'event_time': event_time,
            'status': 'VERIFIED'
        })
        
        return {
            'status': 'VERIFIED',
            'event_hash': event_hash,
            'timestamp': event_time.isoformat()
        }
    
    def detect_gaps(self, current_time: datetime) -> List[Dict[str, Any]]:
        """
        Detect gaps in event sequence.
        
        Args:
            current_time: Current time to check against
        
        Returns:
            List of gap dictionaries
        """
        gaps = []
        last_event_time = max(
            datetime.fromisoformat(t) for t in self.last_events.values()
        ) if self.last_events else current_time - self.cadence * 3
        
        if last_event_time + self.cadence + self.variance < current_time:
            gaps.append({
                'gap_start': last_event_time,
                'gap_end': current_time,
                'missing_count': int(
                    (current_time - last_event_time).total_seconds() / 
                    self.cadence.total_seconds()
                ),
                'severity': 'HIGH' if gaps[0]['missing_count'] > 10 else 'MEDIUM'
            })
        
        return gaps


def process_telemetry_stream(events_file: str) -> Dict[str, Any]:
    """
    Process a stream of telemetry events with replay protection.
    
    Args:
        events_file: Path to JSONL events file
    
    Returns:
        Processing summary
    """
    guard = ReplayGuard()
    results = []
    
    with open(events_file, 'r') as f:
        for line in f:
            event = json.loads(line.strip())
            result = guard.verify_event(event)
            results.append(result)
            
            if result['status'] != 'VERIFIED':
                print(f"⚠️  {result['reason']}")
                print(f"    Original: {result.get('original_time')}")
                print(f"    Attack: {result.get('attack_time')}")
    
    # Detect final gaps
    current_time = datetime.now()
    gaps = guard.detect_gaps(current_time)
    
    return {
        'total_events': len(results),
        'verified': sum(1 for r in results if r['status'] == 'VERIFIED'),
        'replay_attacks': sum(1 for r in results if r['status'] == 'REPLAY_DETECTED'),
        'out_of_order': sum(1 for r in results if r['status'] == 'OUT_OF_ORDER'),
        'gaps': gaps,
        'integrity': 'COMPROMISED' if any(r['status'] != 'VERIFIED' for r in results) else 'INTEGRITY_VERIFIED'
    }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: chain_replay_guard.py <command> [options]")
        print("Commands:")
        print("  monitor <file>   Monitor events in file")
        print("  stream <file>    Stream process events")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command in ['monitor', 'stream'] and len(sys.argv) >= 3:
        summary = process_telemetry_stream(sys.argv[2])
        print(json.dumps(summary, indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
