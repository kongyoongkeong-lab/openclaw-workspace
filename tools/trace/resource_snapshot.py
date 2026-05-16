#!/usr/bin/env python3
"""
Resource Snapshot Capture
Captures GPU/VRAM/CPU context at phase boundaries
"""

import subprocess
import time

def take_resource_snapshot() -> dict:
    """
    Capture system resources at phase transition
    Returns snapshot dict
    """
    snapshot = {
        "ts": time.time(),
        "gpu_utilization": None,
        "vram_usage": None,
        "cpu_usage": None,
        "memory_usage": None
    }
    
    try:
        # Run GPU check script (from injected path)
        result = subprocess.run(
            ["/home/jason/check_gpu.sh"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "utilization:" in line:
                    snapshot["gpu_utilization"] = float(line.split(":")[-1].strip())
                elif "vram:" in line:
                    snapshot["vram_usage"] = float(line.split(":")[-1].strip())
                elif "memory:" in line:
                    snapshot["memory_usage"] = float(line.split(":")[-1].strip())
                    
    except Exception as e:
        snapshot["error"] = str(e)
    
    return snapshot

# Auto-trace resource snapshot at phase boundaries
def trace_phase_boundary(event_name: str, snapshot: dict = None):
    """
    Record phase boundary event with optional resource snapshot
    Usage: trace_phase_boundary("INTEL_PHASE_START")
    """
    snapshot = snapshot or take_resource_snapshot()
    
    event = {
        "event": f"PHASE_{event_name}",
        "ts": time.time(),
        "snapshot": snapshot
    }
    
    from .event_store import append_event
    append_event(event)
    return event

if __name__ == "__main__":
    # Test snapshot
    snap = take_resource_snapshot()
    print(f"Snapshot: {snap}")
