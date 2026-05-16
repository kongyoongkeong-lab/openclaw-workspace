#!/usr/bin/env python3
"""
Replay Kernel v0 — CLI Entrypoint
Replay Kernel v0 — Deterministic State Machine
"""

import json
import sys
from datetime import datetime, timezone

from events.schema import Event, EventType, make_event
from kernel.replay import ReplayKernel, create_kernel
from kernel.state import save_state, load_state, StateValidator

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Replay Kernel v0 CLI")
    parser.add_argument("command", choices=["init", "log", "replay", "export", "load", "validate"])
    parser.add_argument("--events", type=str, help="JSON lines with events")
    parser.add_argument("--state-file", type=str, help="Path to state file")
    parser.add_argument("--target-time", type=str, help="ISO timestamp to replay up to")
    args = parser.parse_args()
    
    kernel = create_kernel()
    
    if args.command == "init":
        print("Replay Kernel initialized.")
        print("Ready to receive events.")
    
    elif args.command == "log":
        if not args.events:
            print("Error: --events required for 'log' command")
            sys.exit(1)
        
        with open(args.events, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse log line: {event_id}|{timestamp}|{type}|{payload}
                    parts = line.split("|")
                    event_id = parts[0]
                    timestamp = datetime.fromisoformat(parts[1])
                    event_type_str = parts[2]
                    payload = json.loads(parts[3]) if len(parts) > 3 else {}
                    
                    event_type = EventType(event_type_str)
                    event = Event(
                        event_id=event_id,
                        timestamp=timestamp,
                        event_type=event_type,
                        payload=payload,
                    )
                    kernel.append_event(event)
                    
                    print(f"[LOG] {event_id} | {event_type_str} | {json.dumps(payload)}")
                    
                except Exception as e:
                    print(f"[ERROR] Failed to parse line: {line}")
                    print(f"  {e}", file=sys.stderr)
    
    elif args.command == "replay":
        state = kernel.replay(target_time=args.target_time)
        print("Replayed state:")
        print(json.dumps(state.to_dict(), indent=2, default=str))
    
    elif args.command == "export":
        lines = kernel.export_log()
        print("\n".join(lines))
    
    elif args.command == "load":
        if not args.state_file:
            print("Error: --state-file required for 'load' command")
            sys.exit(1)
        
        kernel.load_log(open(args.state_file, "r").readlines())
        print(f"Loaded {len(kernel.event_log)} events from {args.state_file}")
    
    elif args.command == "validate":
        if not args.state_file:
            print("Error: --state-file required for 'validate' command")
            sys.exit(1)
        
        state_file = args.state_file
        
        # Compute expected hash
        state = kernel.replay()
        expected_hash = StateValidator.compute_hash(state)
        
        # Load saved state and compare
        saved_state = load_state(state_file)
        saved_hash = StateValidator.compute_hash(saved_state)
        
        if expected_hash == saved_hash:
            print(f"[PASS] State hashes match: {expected_hash[:8]}...")
        else:
            print(f"[FAIL] State hashes differ:")
            print(f"  Expected: {expected_hash}")
            print(f"  Saved: {saved_hash}")
            sys.exit(1)

if __name__ == "__main__":
    main()
