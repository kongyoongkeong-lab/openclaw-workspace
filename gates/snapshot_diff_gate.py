import hashlib
import json
from typing import Dict, Any


def hash_snapshot(snapshot: Dict[str, Any]) -> str:
 """Deterministic snapshot hashing"""
 encoded = json.dumps(snapshot, sort_keys=True).encode()
 return hashlib.sha256(encoded).hexdigest()


def compare_snapshots(prev: Dict[str, Any], curr: Dict[str, Any]) -> Dict[str, Any]:
 prev_hash = hash_snapshot(prev)
 curr_hash = hash_snapshot(curr)

 return {
     "previous_hash": prev_hash,
     "current_hash": curr_hash,
     "changed": prev_hash != curr_hash,
     "status": "BEHAVIOR_CHANGE" if prev_hash != curr_hash else "STABLE"
 }
