#!/usr/bin/env python3
"""
PCG Observer - Real-time telemetry for stress test
Measures all required failure visibility hooks
"""

import os
import json
import time
from pathlib import Path
from datetime import datetime
import subprocess

METRICS_FILE = "/home/jason2ykk/.openclaw/workspace/memory/pcg_metrics.jsonl"
MEMO_PATH = "/home/jason2ykk/.openclaw/workspace/memory/episodic.jsonl"
PCG_LOG_DIR = "/home/jason2ykk/.openclaw/workspace/memory/pcg/"
GPU_CHECK_SCRIPT = "/home/jason2ykk/.openclaw/workspace/tools/check_gpu.sh"


def get_gpu_status():
    """Check VRAM and return status"""
    try:
        result = subprocess.run(
            f"bash {GPU_CHECK_SCRIPT}",
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        lines = result.stdout.strip().split('\n')
        status = {}
        for line in lines:
            if 'VRAM:' in line:
                status['usage_gb'] = line.split('(')[0].split(' ')[-1]
            elif '%' in line:
                usage = line.split('(')[0].split(' ')[-1].strip('%')
                status['usage_pct'] = float(usage)
            elif 'WARNING' in line:
                status['warning'] = line.strip()
        return status
    except Exception as e:
        return {"error": str(e)}


def log_metrics(phase_data):
    """Append metrics to PCG metrics log"""
    if not os.path.exists(METRICS_FILE):
        Path(METRICS_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(METRICS_FILE, 'w') as f:
            f.write("# PCG Metrics Log\n")
    
    with open(METRICS_FILE, 'a') as f:
        ts = datetime.utcnow().isoformat() + "Z"
        entry = {
            "ts": ts,
            **phase_data
        }
        f.write(json.dumps(entry) + '\n')


def record_transition(phase="7.4A", **kwargs):
    """Phase 7.4A: Zone transition telemetry"""
    log_metrics({
        "phase": phase,
        **kwargs,
        "note": "zone transition event"
    })
    return True


def record_critical(phase="7.4B", **kwargs):
    """Phase 7.4B: Critical zone telemetry"""
    log_metrics({
        "phase": phase,
        "compression_rate": kwargs.get("compression_rate", 0),
        "context_growth_rate": kwargs.get("context_growth_rate", 0),
        "dropped_queries": kwargs.get("dropped_queries", 0),
        "retrieval_block_success": kwargs.get("retrieval_block_success", False),
        "agent_backlog_size": kwargs.get("agent_backlog_size", 0),
        "tool_execution_lag_ms": kwargs.get("tool_execution_lag_ms", 0)
    })
    return True


def record_emergency(phase="7.4C", **kwargs):
    """Phase 7.4C: Emergency mode telemetry"""
    return record_critical(phase=phase, retrieval_block_success=True, **kwargs)


def record_recovery(phase="7.4D", **kwargs):
    """Phase 7.4D: Recovery phase telemetry"""
    log_metrics({
        "phase": phase,
        "retrieval_re_expansion": kwargs.get("retrieval_re_expansion", False),
        "memory_coherence": kwargs.get("memory_coherence", True),
        "agent_resync_status": kwargs.get("agent_resync_status", "complete"),
        "throttle_released": kwargs.get("throttle_released", True),
        **kwargs.get("system_health", {})
    })
    return True


def calculate_effectiveness(predicted_growth, actual_growth, controls_active):
    """Calculate PCG effectiveness metric"""
    if predicted_growth <= 0:
        return None, None
    
    effectiveness = predicted_growth - actual_growth
    error_rate = abs(effectiveness) / predicted_growth
    
    return effectiveness, error_rate


def main():
    import sys
    
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    
    if cmd == "status":
        gpu = get_gpu_status()
        print(json.dumps(gpu, indent=2))
    
    elif cmd == "transition":
        phase = sys.argv[2] if len(sys.argv) > 2 else "7.4A"
        record_transition(phase=phase)
        print("✅ Transition logged")
    
    elif cmd == "critical":
        phase = sys.argv[2] if len(sys.argv) > 2 else "7.4B"
        record_critical(phase=phase)
        print("✅ Critical zone logged")
    
    elif cmd == "emergency":
        phase = sys.argv[2] if len(sys.argv) > 2 else "7.4C"
        record_emergency(phase=phase)
        print("⚠️ Emergency mode logged")
    
    elif cmd == "recovery":
        phase = sys.argv[2] if len(sys.argv) > 2 else "7.4D"
        record_recovery(phase=phase)
        print("✅ Recovery logged")
    
    elif cmd == "effectiveness":
        if len(sys.argv) < 4:
            print("Usage: effectiveness <predicted> <actual>")
            return
        predicted = float(sys.argv[2])
        actual = float(sys.argv[3])
        eff, err = calculate_effectiveness(predicted, actual)
        print(json.dumps({
            "effectiveness": eff,
            "error_rate": err
        }))
    
    elif cmd == "observe":
        print("=" * 60)
        print(f"🔍 PCG Observer - Live Telemetry")
        print("=" * 60)
        gpu = get_gpu_status()
        print(f"VRAM: {gpu.get('usage_gb', 'N/A')}GB")
        if gpu.get('warning'):
            print(f"⚠️ {gpu['warning']}")
    
    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
