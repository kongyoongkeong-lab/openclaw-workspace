#!/usr/bin/env python3
import json

events = []
with open('/home/jason2ykk/.openclaw/workspace/memory/episodic.jsonl') as f:
    for line in f:
        events.append(json.loads(line.strip()))

test_events = [e for e in events if e['event_id'].startswith('test_')]
print(f'Total episodic entries: {len(events)}')
print(f'Test events injected: {len(test_events)}')
print()
print('Sample test events:')
for e in test_events[:3]:
    print(f"  {e['event_id']}: {e['content'][:60]}...")
