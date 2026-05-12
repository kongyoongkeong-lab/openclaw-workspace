#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pentagon Alerting Layer - Binary Dispatcher
Fail-silent behavior. No blocking calls.

read → emit → exit
"""

import json
import os
import sys
import time
from datetime import datetime

# Paths
STATE_FILE = os.environ.get('ALERT_STATE', '/home/jason2ykk/.openclaw/workspace/runtime_logs/state/alert_state.json')
LOGS_DIR = '/home/jason2ykk/.openclaw/workspace/runtime_logs/logs'
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '')


def ensure_dirs():
    """Create directories if missing."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)


def read_state():
    """Read alert state."""
    try:
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "gpu_alert_active": False,
            "timeout_120s": False,
            "compression_alert_active": False,
            "path_integrity_alert_active": False,
            "workspace_alert_active": False,
            "last_gpu_alert": None,
            "last_timeout_alert": None,
            "last_compression_alert": None,
            "last_path_alert": None,
            "last_workspace_alert": None
        }


def write_state(state):
    """Write state atomically."""
    ensure_dirs()
    temp_file = STATE_FILE + '.tmp'
    try:
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, STATE_FILE)
    except Exception:
        if os.path.exists(temp_file):
            os.remove(temp_file)


def send_telegram(message):
    """Send Telegram message. Fail-silent."""
    if not TELEGRAM_TOKEN:
        return
    
    try:
        import requests
        
        url = 'https://api.telegram.org/bot{token}/sendMessage'.format(token=TELEGRAM_TOKEN)
        payload = {
            'chat_id': os.environ.get('TELEGRAM_CHAT_ID', '-1001534035221'),
            'text': message,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, json=payload, timeout=5)
        
        if response.status_code == 200:
            return True, "Telegram message sent"
        else:
            return False, f"Telegram HTTP {response.status_code}"
            
    except Exception as e:
        # Fail-silent: don't block, just log
        log_path = os.path.join(LOGS_DIR, 'telegram_error_{}.log'.format(int(datetime.now().timestamp())))
        with open(log_path, 'w') as f:
            f.write("Telegram Error: {}\n".format(str(e)))
        return False, "Telegram error (logged)"


def dispatch_all():
    """Dispatch all active alerts. Fail-silent."""
    state = read_state()
    results = []
    
    # Check and dispatch GPU alert
    if state.get("gpu_alert_active"):
        message = "🚀 GPU ALERT: High utilization detected\n"
        message += "```json\n"
        message += "  {{\n"
        message += "    \"severity\": \"INFO\",\n"
        message += "    \"type\": \"GPU_UTILIZATION\",\n"
        message += "    \"threshold\": \"70-85% sustained, 95% burst\",\n"
        message += "    \"cooldown\": \"60s\"\n"
        message += "  }}\n"
        message += "```"
        sent, msg = send_telegram(message)
        results.append(("GPU", sent, msg))
    
    # Check and dispatch Timeout alert
    if state.get("timeout_120s"):
        message = "⏱ TIMEOUT ALERT: Request timeout detected\n"
        message += "```json\n"
        message += "  {{\n"
        message += "    \"severity\": \"WARN\",\n"
        message += "    \"type\": \"TIMEOUT\",\n"
        message += "    \"cooldown\": \"120s\"\n"
        message += "  }}\n"
        message += "```"
        sent, msg = send_telegram(message)
        results.append(("Timeout", sent, msg))
    
    # Check and dispatch Compression alert
    if state.get("compression_alert_active"):
        message = "📦 COMPRESSION ALERT: Compression ratio threshold exceeded\n"
        message += "```json\n"
        message += "  {{\n"
        message += "    \"severity\": \"WARN\",\n"
        message += "    \"type\": \"COMPRESSION\",\n"
        message += "    \"cooldown\": \"300s\"\n"
        message += "  }}\n"
        message += "```"
        sent, msg = send_telegram(message)
        results.append(("Compression", sent, msg))
    
    # Check and dispatch Path Integrity alert (CRITICAL)
    if state.get("path_integrity_alert_active"):
        message = "🛡 PATH CORRUPTION ALERT: Path integrity violated\n"
        message += "```json\n"
        message += "  {{\n"
        message += "    \"severity\": \"CRITICAL\",\n"
        message += "    \"type\": \"PATH_INTEGRITY\",\n"
        message += "    \"cooldown\": \"immediate (critical)\"\n"
        message += "  }}\n"
        message += "```"
        sent, msg = send_telegram(message)
        results.append(("Path", sent, msg))
    
    # Check and dispatch Workspace alert (CRITICAL)
    if state.get("workspace_alert_active"):
        message = "🏢 WORKSPACE ALERT: Workspace mutation detected\n"
        message += "```json\n"
        message += "  {{\n"
        message += "    \"severity\": \"CRITICAL\",\n"
        message += "    \"type\": \"WORKSPACE_INTEGRITY\",\n"
        message += "    \"cooldown\": \"immediate (critical)\"\n"
        message += "  }}\n"
        message += "```"
        sent, msg = send_telegram(message)
        results.append(("Workspace", sent, msg))
    
    return results


def main():
    """Main entry point. Fail-silent."""
    print("Pentagon Alert Dispatcher starting...")
    print("Fail-silent mode enabled.")
    
    results = dispatch_all()
    
    for alert_type, sent, msg in results:
        print("{}: {} - {}".format(alert_type, sent, msg))
    
    print("Dispatch complete.")


if __name__ == "__main__":
    main()