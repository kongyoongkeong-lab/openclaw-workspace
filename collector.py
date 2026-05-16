"""
Reality Alignment Sensor (RAS) MVP
Minimal Signal Adapter - 3-Input Truth Sensor

Architecture:
┌─────────────┐
│   CI Signal │  ← GitHub Actions webhook/API
└─────────────┘
         │
         ▼
┌──────────────────────────┐
│   Runtime Signal         │  ← Discord bot heartbeat
└──────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│   Divergence Logic       │  ← ci != runtime
└──────────────────────────┘
         │
         ▼
   Stability Dashboard

O(1) Complexity - No Cron, No Jenkins Parser, No Full Logs
"""

import time
from datetime import datetime, timezone
from typing import Optional, Literal


class MinimalSignalAdapter:
    """
    Minimal Truth Sources (MTS) - 3-Input Reality Sensor
    
    Core Functions:
    1. get_ci_status() - GitHub Actions binary signal
    2. get_runtime_status() - Discord bot heartbeat
    3. compute_divergence() - Divergence detection
    
    Constraints:
    - NO cron scheduling
    - NO Jenkins/GitLab parser
    - NO full log ingestion
    - NO distributed telemetry
    """
    
    def __init__(self):
        """Initialize signal adapters."""
        self.last_ci_status: Optional[int] = None
        self.last_runtime_status: Optional[int] = None
        self.last_ci_timestamp: Optional[str] = None
        self.last_runtime_timestamp: Optional[str] = None
        self.last_disconnect: Optional[str] = None
    
    def get_ci_status(self) -> dict[str, ...]:
        """
        CI Signal Extraction
        Source: GitHub Actions webhook or API
        
        Extracts ONLY:
        - success/fail → ci: 1|0
        - timestamp
        - Ignores: Jenkins, GitLab, full log parsing
        
        Returns:
            {
                "ci": 0|1,
                "ci_last_run": "timestamp"
            }
        """
        # SIMULATED - In production, this would call:
        # - GitHub Actions API: https://api.github.com/repos/OWNER/REPO/actions/runs
        # - Or webhook payload parsing
        # 
        # For MVP, we use a simulated check against local git state
        # or GitHub status file if available.
        
        try:
            # Check for CI status file or simulate
            status_file = "/tmp/.ci_status"
            if status_file and __import__("os").path.exists(status_file):
                with open(status_file, "r") as f:
                    status_str = f.read().strip()
                    ci_status = 1 if status_str == "success" else 0
                    timestamp = datetime.now(timezone.utc).isoformat()
            else:
                # Default to success if no signal (conservative default)
                ci_status = 1
                timestamp = datetime.now(timezone.utc).isoformat()
            
            self.last_ci_status = ci_status
            self.last_ci_timestamp = timestamp
            
            return {
                "ci": ci_status,
                "ci_last_run": timestamp
            }
            
        except Exception as e:
            # Fail-open: assume success unless evidence of failure
            print(f"[CI-Signal] Error: {e}")
            return {
                "ci": 1,  # conservative default
                "ci_last_run": datetime.now(timezone.utc).isoformat()
            }
    
    def get_runtime_status(self) -> dict[str, ...]:
        """
        Runtime Signal Extraction
        Source: Discord bot status or any simple heartbeat
        
        Extracts ONLY:
        - bot alive → 1
        - crashed/disconnected → 0
        
        Returns:
            {
                "runtime": 0|1,
                "last_disconnect": "timestamp" (if crashed)
            }
        """
        # SIMULATED - In production, this would check:
        # - Discord client connection
        # - TCP socket health
        # - Process status
        # - Ping latency
        # 
        # For MVP, we check a simulated heartbeat file or socket
        
        heartbeat_file = "/tmp/.bot_heartbeat"
        try:
            if heartbeat_file and __import__("os").path.exists(heartbeat_file):
                with open(heartbeat_file, "r") as f:
                    heartbeat = f.read().strip()
                    runtime_status = 1 if heartbeat == "alive" else 0
                    timestamp = datetime.now(timezone.utc).isoformat()
                    
                    if runtime_status == 0 and self.last_disconnect is None:
                        self.last_disconnect = timestamp
                    
                    self.last_runtime_status = runtime_status
                    self.last_runtime_timestamp = timestamp
                    
                    return {
                        "runtime": runtime_status,
                        "last_disconnect": self.last_disconnect
                    }
            else:
                # No heartbeat file - assume alive (default)
                return {
                    "runtime": 1,
                    "last_disconnect": None
                }
                
        except Exception as e:
            # Fail-open: assume runtime is alive
            print(f"[Runtime-Signal] Error: {e}")
            return {
                "runtime": 1,
                "last_disconnect": self.last_disconnect
            }
    
    def compute_divergence(self, ci_signal: Optional[dict] = None, 
                           runtime_signal: Optional[dict] = None) -> dict[str, ...]:
        """
        Divergence Logic
        divergence = 1 if ci != runtime else 0
        
        Returns:
            {
                "ci": 0|1,
                "runtime": 0|1,
                "divergence": 0|1,
                "timestamp": "ISO8601"
            }
        """
        # Use provided signals or fetch latest
        if ci_signal is None:
            ci_signal = self.get_ci_status()
        if runtime_signal is None:
            runtime_signal = self.get_runtime_status()
        
        ci = ci_signal["ci"]
        runtime = runtime_signal["runtime"]
        
        divergence = 1 if ci != runtime else 0
        
        # Update internal state
        self.last_ci_status = ci
        self.last_runtime_status = runtime
        
        return {
            "ci": ci,
            "runtime": runtime,
            "divergence": divergence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Convenience function for immediate use
def assess_reality() -> dict[str, ...]:
    """
    Assess Reality Alignment - Single call to RAS
    
    Returns divergence report.
    """
    adapter = MinimalSignalAdapter()
    return adapter.compute_divergence()


def main():
    """
    RAS MVP Entry Point
    
    Usage:
    python collector.py
    
    Output:
    {
        "ci": 1,
        "runtime": 1,
        "divergence": 0,
        "timestamp": "2026-05-15T04:07:00+08:00"
    }
    """
    print("Reality Alignment Sensor (RAS) - MVP")
    print("=" * 40)
    
    report = assess_reality()
    
    print(f"CI Status:      {report['ci']}")
    print(f"Runtime Status: {report['runtime']}")
    print(f"Divergence:     {report['divergence']}")
    print(f"Timestamp:      {report['timestamp']}")
    
    if report["divergence"] == 1:
        print("\n⚠️  REALITY DIVERGENCE DETECTED!")
        print("   CI reports:", report['ci'])
        print("   Runtime:", report['runtime'])
    
    return report


if __name__ == "__main__":
    main()
