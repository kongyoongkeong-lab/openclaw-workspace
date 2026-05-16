import hashlib
import json


def topology_hash(workflow: dict) -> str:
 """
 Hash only structural elements:
 - nodes (agents/tools)
 - edges (execution order)
 """
 structure = {
     "nodes": workflow.get("nodes", []),
     "edges": workflow.get("edges", [])
 }

 encoded = json.dumps(structure, sort_keys=True).encode()
 return hashlib.sha256(encoded).hexdigest()


def validate_topology(current: dict, baseline_hash: str) -> dict:
 curr_hash = topology_hash(current)

 return {
     "current_hash": curr_hash,
     "baseline_hash": baseline_hash,
     "valid": curr_hash == baseline_hash,
     "status": "PASS" if curr_hash == baseline_hash else "FAIL"
 }
