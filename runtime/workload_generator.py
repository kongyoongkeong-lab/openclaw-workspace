#!/usr/bin/env python3
"""
Phase A Workload Generator
Injects realistic mixed operational load during controlled production.
"""
import json
import time
import random
import uuid
from datetime import datetime, timezone

CONFIG_PATH = "/home/jason2ykk/.openclaw/workspace/runtime/phase_a_config.json"
STATUS_PATH = "/home/jason2ykk/.openclaw/workspace/runtime/phase_a_status.jsonl"

def generate_semantic_retrieval_task():
    """Moderate semantic retrieval task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "semantic_retrieval",
        "priority": random.randint(1, 3),
        "query": f"Retrieve knowledge about {random.choice(['telemetry', 'compression', 'spg', 'governance'])}",
        "top_k": random.choice([2, 3]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_episodic_replay_task():
    """Episodic memory replay task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "episodic_replay",
        "priority": random.randint(1, 2),
        "content": f"Replay episodic event #{random.randint(1, 13)}",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_governance_query_task():
    """Governance/SPG query task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "governance_query",
        "priority": 1,
        "query": f"Query SPG state for control_delta metric",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_reasoning_task():
    """Orchestration/reasoning prompt task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "reasoning",
        "priority": random.randint(1, 3),
        "prompt": f"Analyze runtime telemetry and recommend action: {random.choice(['monitor', 'adapt', 'throttle'])}",
        "context_size": random.randint(100, 3000),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_compression_decision_task():
    """Compression decision task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "compression_decision",
        "priority": 2,
        "episodes_to_evaluate": random.randint(1, 5),
        "aggressiveness": random.choice(["moderate", "conservative"]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_telemetry_collection_task():
    """Background telemetry collection"""
    return {
        "id": str(uuid.uuid4()),
        "type": "telemetry_collection",
        "priority": 1,
        "metrics": ["event_loop_p99", "queue_depth", "context_usage", "gpu_utilization"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_alert_evaluation_task():
    """Alert evaluation task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "alert_evaluation",
        "priority": 1,
        "check_runtime": True,
        "check_governance": True,
        "check_memory": True,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_queue_management_task():
    """Queue management task"""
    return {
        "id": str(uuid.uuid4()),
        "type": "queue_management",
        "priority": 1,
        "action": random.choice(["drain", "throttle", "flush"]),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_workload_batch(num_tasks=8):
    """Generate a batch of mixed workload"""
    task_types = [
        generate_semantic_retrieval_task,
        generate_episodic_replay_task,
        generate_governance_query_task,
        generate_reasoning_task,
        generate_compression_decision_task,
        generate_telemetry_collection_task,
        generate_alert_evaluation_task,
        generate_queue_management_task
    ]
    
    return [func() for func in random.sample(task_types, min(num_tasks, len(task_types)))]

def update_status(status_path, tasks):
    """Update runtime status file"""
    if not tasks:
        return
    
    last_status = []
    try:
        with open(status_path, 'r') as f:
            for line in f:
                last_status.append(json.loads(line.strip()))
    except:
        pass
    
    if last_status:
        last = last_status[-1]
        last["tasks_generated"] = len(tasks)
        last["tasks"] = [t.get("id", "")[:8] for t in tasks[:5]]
        
        with open(status_path, 'w') as f:
            for entry in last_status + [last]:
                f.write(json.dumps(entry) + "\n")
    else:
        with open(status_path, 'a') as f:
            f.write(json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "phase": "A",
                "status": "RUNNING",
                "tasks_generated": len(tasks),
                "tasks": [t.get("id", "")[:8] for t in tasks[:5]]
            }) + "\n")

if __name__ == "__main__":
    import sys
    
    # Generate initial workload
    batch = generate_workload_batch(num_tasks=8)
    print(f"Generated {len(batch)} tasks for Phase A")
    for task in batch:
        print(f"  - {task['type']}: {task.get('query', task.get('content', 'N/A'))[:50]}...")
    
    # Save initial status
    update_status(STATUS_PATH, batch)
    
    print("Phase A workload injection complete.")
    print("Telemetry collection active. Awaiting runtime feedback.")