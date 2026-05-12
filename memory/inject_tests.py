#!/usr/bin/env python3
import json
from datetime import datetime

events = [
    {'timestamp': '2026-05-09T10:15:00+08:00', 'event_id': 'test_001', 'source': 'compression_test', 'type': 'episodic', 'context': 'compression_validation', 'content': 'Test event 1: GPU utilization 71% VRAM monitoring active'},
    {'timestamp': '2026-05-09T10:15:01+08:00', 'event_id': 'test_002', 'source': 'compression_test', 'type': 'episodic', 'context': 'compression_validation', 'content': 'Test event 2: Context window 61% Semantic memory 1001 entries'},
    {'timestamp': '2026-05-09T10:15:02+08:00', 'event_id': 'test_003', 'source': 'compression_test', 'type': 'episodic', 'context': 'compression_validation', 'content': 'Test event 3: Compression threshold 2501 lines approaching'},
]

for event in events:
    with open('/home/jason2ykk/.openclaw/workspace/memory/episodic.jsonl', 'a') as f:
        f.write(json.dumps(event) + '\n')

print(f'Injected {len(events)} test events')
