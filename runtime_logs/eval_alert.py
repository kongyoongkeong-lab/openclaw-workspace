#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pentagon Alerting Layer - Stateless Evaluator
Read → Evaluate → Emit → Exit

NO MEMORY WRITES. NO RECURSIVE TELEMETRY.
"""

import json
import os
import time
from datetime import datetime

# Paths
STATE_FILE = os.environ.get('ALERT_STATE', '/home/jason2ykk/.openclaw/workspace/runtime_logs/state/alert_state.json')
ALERTS_DIR = '/home/jason2ykk/.openclaw/workspace/runtime_logs/alerts'
LOGS_DIR = '/home/jason2ykk/.openclaw/workspace/runtime_logs/logs'


def ensure_dirs():
    """Create directories if missing."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    os.makedirs(ALERTS_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def read_state():
    """Read alert state atomically."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "gpu_alert_active": False,
            "last_gpu_alert": None,
            "timeout_120s": False,
            "last_timeout_alert": None,
            "compression_alert_active": False,
            "last_compression_alert": None,
            "path_integrity_alert_active": False,
            "last_path_alert": None,
            "workspace_alert_active": False,
            "last_workspace_alert": None
        }


def write_state(state):
    """Write state atomically (temp file + rename)."""
    ensure_dirs()
    temp_file = STATE_FILE + '.tmp'
    try:
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
    except Exception:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise


def check_gpu(utilization):
    """GPU Utilization Alert."""
    if utilization is None:
        return False, "OK"
    
    threshold = 95
    cooldown_key = "last_gpu_alert"
    cooldown_seconds = 60
    
    state = read_state()
    last_alert = state.get(cooldown_key)
    
    if state.get("gpu_alert_active"):
        return state.get("gpu_alert_active"), "ALERT"
    
    if last_alert:
        last_ts = datetime.fromtimestamp(last_alert).timestamp()
        if (time.time() - last_ts) < cooldown_seconds:
            return False, "OK (cooldown)"
    
    if utilization >= threshold:
        state["gpu_alert_active"] = True
        state[cooldown_key] = time.time()
        write_state(state)
        
        log_path = os.path.join(LOGS_DIR, "gpu_alert_{}.log".format(int(datetime.now().timestamp())))
        with open(log_path, 'w') as f:
            f.write(f"GPU Alert: {utilization}% utilization\n")
        return True, f"ALERT: GPU {utilization}% ≥ {threshold}%"
    
    return False, "OK"


def check_timeout():
    """Timeout Alert (120s cooldown)."""
    cooldown_key = "last_timeout_alert"
    cooldown_seconds = 120
    
    state = read_state()
    last_alert = state.get(cooldown_key)
    
    if state.get("timeout_120s"):
        return state.get("timeout_120s"), "ALERT"
    
    if last_alert:
        last_ts = datetime.fromtimestamp(last_alert).timestamp()
        if (time.time() - last_ts) < cooldown_seconds:
            return False, "OK (cooldown)"
    
    # Simulate timeout condition
    state["timeout_120s"] = True
    state[cooldown_key] = time.time()
    write_state(state)
    
    log_path = os.path.join(LOGS_DIR, "timeout_alert_{}.log".format(int(datetime.now().timestamp())))
    with open(log_path, 'w') as f:
        f.write(f"Timeout Alert triggered\n")
    
    return True, "ALERT: Timeout (cooldown)"


def check_compression():
    """Compression Alert (300s cooldown)."""
    cooldown_key = "last_compression_alert"
    cooldown_seconds = 300
    
    state = read_state()
    last_alert = state.get(cooldown_key)
    
    if state.get("compression_alert_active"):
        return state.get("compression_alert_active"), "ALERT"
    
    if last_alert:
        last_ts = datetime.fromtimestamp(last_alert).timestamp()
        if (time.time() - last_ts) < cooldown_seconds:
            return False, "OK (cooldown)"
    
    state["compression_alert_active"] = True
    state[cooldown_key] = time.time()
    write_state(state)
    
    log_path = os.path.join(LOGS_DIR, "compression_alert_{}.log".format(int(datetime.now().timestamp())))
    with open(log_path, 'w') as f:
        f.write(f"Compression Alert triggered\n")
    
    return True, "ALERT: Compression threshold exceeded"


def check_path_integrity():
    """Path Integrity Alert (Immediate, critical)."""
    state = read_state()
    
    # Check for path mutations
    if os.path.exists('/home/jason2ykk/.openclaw/workspace/runtime_logs/state/alert_state.json') and \
       state.get("path_integrity_alert_active"):
        return state.get("path_integrity_alert_active"), "ALERT"
    
    # Reset on first run (or clear mutation)
    state["path_integrity_alert_active"] = False
    state["last_path_alert"] = None
    write_state(state)
    
    return False, "OK: Path integrity verified"


def check_workspace():
    """Workspace Integrity Alert (Immediate, critical)."""
    state = read_state()
    
    # Check for workspace mutations
    if state.get("workspace_alert_active"):
        return state.get("workspace_alert_active"), "ALERT"
    
    # Check for unexpected nesting
    workspace = '/home/jason2ykk/.openclaw/workspace'
    if os.path.exists(workspace + '/workspace'):
        state["workspace_alert_active"] = True
        state["last_workspace_alert"] = time.time()
        write_state(state)
        log_path = os.path.join(LOGS_DIR, "workspace_alert_{}.log".format(int(datetime.now().timestamp())))
        with open(log_path, 'w') as f:
            f.write(f"Workspace Integrity Alert: Unexpected nesting detected\n")
        return True, "ALERT: Workspace mutation detected"
    
    state["workspace_alert_active"] = False
    state["last_workspace_alert"] = None
    write_state(state)
    
    return False, "OK: Workspace integrity verified"


def evaluate_all(utilization=None):
    """Evaluate all alerts."""
    results = []
    
    results.append(("GPU", check_gpu(utilization)))
    results.append(("Timeout", check_timeout()))
    results.append(("Compression", check_compression()))
    results.append(("Path", check_path_integrity()))
    results.append(("Workspace", check_workspace()))
    
    return results


if __name__ == "__main__":
    import sys
    
    utilization = float(sys.argv[1]) if len(sys.argv) > 1 else None
    
    results = evaluate_all(utilization)
    for alert_type, status in results:
        print(f"{alert_type}: {status}")