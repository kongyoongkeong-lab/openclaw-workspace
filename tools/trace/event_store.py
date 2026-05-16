#!/usr/bin/env python3
"""
Event Sourcing Storage Layer
Phase 1: JSONL append-only (portable, schema-migration ready)
"""

import json
import os
from datetime import datetime
from pathlib import Path

TRACES_DIR = Path("/home/jason2ykk/.openclaw/workspace/traces")
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
CURRENT_FILE = TRACES_DIR / f"{CURRENT_DATE}.jsonl"

def ensure_store():
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    if not CURRENT_FILE.exists():
        CURRENT_FILE.touch()

def append_event(event: dict) -> str:
    """Append event to JSONL file. Returns event ID."""
    ensure_store()
    # Generate simple event ID
    event_id = event.get("trace_id", f"e{int(datetime.now().timestamp())}")
    event["_id"] = event_id
    
    # Atomic append
    content = json.dumps(event, ensure_ascii=False) + "\n"
    with open(CURRENT_FILE, "a", encoding="utf-8") as f:
        f.write(content)
    
    return event_id

def get_all_events(limit: int = None) -> list:
    """Read events from current JSONL file."""
    if not CURRENT_FILE.exists():
        return []
    
    events = []
    with open(CURRENT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                events.append(json.loads(line))
    
    if limit:
        events = events[-limit:]
    
    return events

def get_events_by_trace_id(trace_id: str) -> list:
    """Fetch events for a specific trace."""
    events = get_all_events()
    return [e for e in events if e.get("trace_id") == trace_id]

if __name__ == "__main__":
    # Test append
    test_event = {
        "trace_id": "test-001",
        "event": "INIT",
        "ts": datetime.now().isoformat(),
        "msg": "Event store initialized"
    }
    eid = append_event(test_event)
    print(f"Event stored with ID: {eid}")
    
    # Test read
    events = get_events_by_trace_id("test-001")
    print(f"Retrieved events: {events}")
