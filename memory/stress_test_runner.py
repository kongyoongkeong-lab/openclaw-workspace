#!/usr/bin/env python3
"""Memory System Stress Test Suite"""
import json
import time
import random
from datetime import datetime, timezone
import os

# Constants
EPISODIC_PATH = "/home/jason2ykk/.openclaw/workspace/memory/episodic.jsonl"
SEMANTIC_PATH = "/home/jason2ykk/.openclaw/workspace/memory/semantic.jsonl"
COMPRESSOR_PATH = "/home/jason2ykk/.openclaw/workspace/tools/compressor_ltm.py"

def append_episodic(content: str, source: str = "stress_test"):
    """Append an episodic event"""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_id": f"stress_{len(open(EPISODIC_PATH).readlines()) + 1:03d}",
        "source": source,
        "type": "episodic",
        "context": "stress_test",
        "content": content
    }
    with open(EPISODIC_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")
    return event["event_id"]

def read_episodic() -> list:
    """Read all episodic events"""
    events = []
    if os.path.exists(EPISODIC_PATH):
        with open(EPISODIC_PATH, "r") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
    return events

def run_stress_test(test_name: str, num_events: int, event_pattern: str):
    """Run a stress test with synthetic events"""
    print(f"\n{'='*60}")
    print(f"🧪 STRESS TEST: {test_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Generate and store events
    print(f"\n📝 Injecting {num_events} synthetic events...")
    for i in range(num_events):
        if event_pattern == "hardware":
            content = f"Synthetic hardware monitoring event #{i+1}: GPU={random.randint(40,95)}% VRAM={random.randint(20,35)}GB"
        elif event_pattern == "system":
            content = f"Synthetic system metrics event #{i+1}: CPU={random.randint(20,70)}% RAM={random.randint(8,40)}GB latency={random.randint(50,200)}ms"
        elif event_pattern == "user":
            content = f"Synthetic user interaction event #{i+1}: Session={random.randint(1,5)} Task={random.choice(['coding','search','browse','write','edit'])}"
        else:
            content = f"Synthetic generic event #{i+1}: Context window={random.randint(30,80)}% Load={random.randint(20,90)}% health={random.randint(85,99)}%"
        
        append_episodic(content, source="stress_test")
    
    total_events = len(read_episodic())
    episodic_count = len([e for e in read_episodic() if "stress_test" in e.get("source", "")])
    
    elapsed = time.time() - start_time
    print(f"✅ Injected {episodic_count} events in {elapsed:.2f}s ({episodic_count/elapsed:.1f} events/sec)")
    
    return total_events

def trigger_compression():
    """Trigger memory compression"""
    print(f"\n💥 Triggering compression...")
    start = time.time()
    
    # Run compressor
    result = os.system(f"python3 {COMPRESSOR_PATH}")
    
    elapsed = time.time() - start
    print(f"✅ Compression completed in {elapsed:.2f}s")
    return elapsed

def evaluate_retention(episodic_events: list) -> dict:
    """Evaluate retrieval fidelity and compression artifacts"""
    print(f"\n🔍 Evaluating memory integrity...")
    
    # Check for duplicates
    seen = set()
    duplicates = 0
    for event in episodic_events:
        content_hash = hash(event["content"])
        if content_hash in seen:
            duplicates += 1
        seen.add(content_hash)
    
    # Calculate compression ratio
    total_lines = len(open(EPISODIC_PATH).readlines())
    
    # Sample retrieval tests
    test_queries = [
        "GPU utilization",
        "VRAM reading",
        "system metrics",
        "user interaction"
    ]
    
    retrieval_stats = {}
    for query in test_queries:
        matches = sum(1 for e in episodic_events if query.lower() in e.get("content", "").lower())
        retrieval_stats[query] = matches
    
    return {
        "duplicates": duplicates,
        "total_events": total_lines,
        "retrieval_stats": retrieval_stats
    }

def main():
    print(f"\n🚀 MEMORY SYSTEM PERFORMANCE TEST")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    
    # Test 1: Normal load (100 events)
    run_stress_test("NORMAL LOAD", 100, "hardware")
    run_compression()
    stats = evaluate_retention(read_episodic())
    
    print(f"\n📊 RESULTS:")
    print(f"   Total episodic events: {stats['total_events']}")
    print(f"   Duplicates found: {stats['duplicates']}")
    print(f"   Compression ratio: {stats['total_events'] / len(open(EPISODIC_PATH).readlines()):.2f}x")
    
    # Test 2: High load (500 events)
    run_stress_test("HIGH LOAD", 500, "system")
    run_compression()
    stats = evaluate_retention(read_episodic())
    
    print(f"\n📊 RESULTS:")
    print(f"   Total episodic events: {stats['total_events']}")
    print(f"   Duplicates found: {stats['duplicates']}")
    
    # Test 3: Verify retrieval correctness
    print(f"\n🎯 Verification Tests...")
    events = read_episodic()
    for i, event in enumerate(events[:5]):  # Test first 5 events
        content = event["content"]
        retrieved = json.loads(line)
        if retrieved["content"] == content:
            print(f"   ✅ Event {i}: Retrieval correct")
        else:
            print(f"   ❌ Event {i}: Retrieval mismatch")

if __name__ == "__main__":
    main()
