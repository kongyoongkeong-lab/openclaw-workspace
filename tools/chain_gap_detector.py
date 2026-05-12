#!/usr/bin/env python3
"""
Gap Detector - Silent Data Loss Prevention
Monitors telemetry cadence and detects missing events.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

# Configuration
EXPECTED_CADENCE = timedelta(minutes=5)
ALERT_THRESHOLD = timedelta(minutes=10)
CRITICAL_THRESHOLD = timedelta(minutes=20)
TELEMETRY_DIR = Path.home() / '.openclaw/workspace/logs'


class GapDetector:
    """
    Detect gaps in telemetry event stream.
    
    Features:
    - Cadence monitoring
    - Gap classification (info/warning/critical)
    - Silent data loss detection
    - Recovery recommendations
    """
    
    def __init__(self):
        self.last_event_time: Optional[datetime] = None
        self.gap_history: List[Dict[str, Any]] = []
        self.cadence_baseline = EXPECTED_CADENCE
        self.alert_count: int = 0
    
    def process_event(self, event_time: datetime, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process event and detect gaps since last event.
        
        Args:
            event_time: Timestamp of current event
            event_data: Event data dictionary
        
        Returns:
            Gap detection result
        """
        result = {
            'event_time': event_time,
            'gap_detected': False,
            'gap_info': None
        }
        
        if self.last_event_time:
            elapsed = event_time - self.last_event_time
            
            if elapsed > ALERT_THRESHOLD:
                severity = 'CRITICAL' if elapsed > CRITICAL_THRESHOLD else 'WARNING'
                result['gap_detected'] = True
                result['gap_info'] = {
                    'severity': severity,
                    'elapsed': elapsed,
                    'missing_events': int(elapsed.total_seconds() / self.cadence_baseline.total_seconds()),
                    'recommendation': self._generate_recommendation(severity, elapsed)
                }
                self.gap_history.append(result['gap_info'])
                self.alert_count += 1
            
            self.last_event_time = event_time
        
        return result
    
    def _generate_recommendation(self, severity: str, elapsed: timedelta) -> str:
        """Generate recovery recommendation based on gap severity."""
        if severity == 'CRITICAL':
            return "URGENT: Check telemetry collection pipeline. Consider increasing buffer size."
        elif severity == 'WARNING':
            return "Monitor: Telemetry cadence below baseline. Verify connection health."
        else:
            return "Info: Normal cadence variation."
    
    def detect_gaps_in_range(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """
        Detect gaps in a time range.
        
        Args:
            start_time: Start of range
            end_time: End of range
        
        Returns:
            List of detected gaps
        """
        gaps = []
        events = self._load_events_from_range(start_time, end_time)
        
        for event in events:
            result = self.process_event(
                datetime.fromisoformat(event['timestamp']),
                event
            )
            if result['gap_detected']:
                gaps.append(result['gap_info'])
        
        return gaps
    
    def _load_events_from_range(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Load events within time range from log files."""
        events = []
        
        for log_file in TELEMETRY_DIR.glob('*.jsonl'):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        event = json.loads(line.strip())
                        event_time = datetime.fromisoformat(event.get('timestamp', ''))
                        if start <= event_time <= end:
                            events.append(event)
            except (json.JSONDecodeError, IOError):
                continue
        
        return events


def analyze_telemetry_health(log_dir: str = None) -> Dict[str, Any]:
    """
    Analyze overall telemetry health.
    
    Args:
        log_dir: Directory containing telemetry logs
    
    Returns:
        Health analysis dictionary
    """
    if log_dir is None:
        log_dir = TELEMETRY_DIR
    
    detector = GapDetector()
    analysis = {
        'log_dir': log_dir,
        'health_score': 100,
        'total_gaps': 0,
        'critical_gaps': 0,
        'warning_gaps': 0,
        'last_analyzed': datetime.now().isoformat(),
        'recommendations': []
    }
    
    # Find most recent event
    max_time = None
    log_files = list(log_dir.glob('*.jsonl'))
    
    if log_files:
        with open(log_files[0], 'r') as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    event_time = datetime.fromisoformat(event.get('timestamp', ''))
                    if max_time is None or event_time > max_time:
                        max_time = event_time
                except (json.JSONDecodeError, KeyError):
                    continue
    
    if max_time:
        # Scan backwards for gaps
        scan_start = max_time - timedelta(hours=1)
        gaps = detector.detect_gaps_in_range(scan_start, max_time)
        
        analysis['total_gaps'] = len(gaps)
        analysis['critical_gaps'] = sum(1 for g in gaps if g['severity'] == 'CRITICAL')
        analysis['warning_gaps'] = sum(1 for g in gaps if g['severity'] == 'WARNING')
        
        if analysis['total_gaps'] > 0:
            analysis['health_score'] = max(0, 100 - analysis['total_gaps'] * 10)
            analysis['recommendations'] = [
                "Investigate gap root cause",
                "Consider increasing telemetry buffer",
                "Verify collection pipeline health"
            ]
    
    return analysis


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: chain_gap_detector.py <command> [options]")
        print("Commands:")
        print("  health [dir]     Analyze telemetry health")
        print("  scan <start> <end>  Scan for gaps in range")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'health':
        log_dir = sys.argv[2] if len(sys.argv) > 2 else None
        analysis = analyze_telemetry_health(log_dir)
        print(json.dumps(analysis, indent=2))
    
    elif command in ['scan', 'detect'] and len(sys.argv) >= 4:
        start_time = sys.argv[2]
        end_time = sys.argv[3]
        detector = GapDetector()
        gaps = detector.detect_gaps_in_range(datetime.fromisoformat(start_time), 
                                            datetime.fromisoformat(end_time))
        print(f"Detected {len(gaps)} gaps:")
        for gap in gaps:
            print(f"  - {gap['severity']}: {gap['elapsed']} missing {gap['missing_events']} events")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == '__main__':
    main()
