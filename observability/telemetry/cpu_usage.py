#!/usr/bin/env python3
"""
CPU Usage Monitor
==================

Non-invasive CPU sampling for workload regime stability analysis.
"""

import time
import os
import json
from pathlib import Path

def get_cpu_percent():
    """Get current CPU usage percentage using /proc/stat."""
    with open('/proc/stat') as f:
        lines = f.readlines()
    
    cpu_line = lines[0]
    parts = cpu_line.split()
    idle = int(parts[4])
    total = sum(int(parts[i]) for i in range(1, 5)) + idle
    return (1.0 - idle / total) * 100

def get_gpu_util():
    """Get NVIDIA GPU utilization from nvidia-smi."""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            lines = [line.strip() for line in result.stdout.strip().split('\n')]
            return int(lines[0]) if lines else 0
    except:
        pass
    return None

if __name__ == '__main__':
    cpu = get_cpu_percent()
    gpu = get_gpu_util()
    print(f"CPU: {cpu:.2f}%, GPU: {gpu or 'N/A'}%")
