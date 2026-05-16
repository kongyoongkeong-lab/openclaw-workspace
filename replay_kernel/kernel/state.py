"""
State Validator — Deterministic Hashing
Replay Kernel v0 — Deterministic State Machine
"""

import hashlib
import json
import sys

sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/replay_kernel")

from kernel.reducer import State
from kernel.reducer import apply_event_batch

class StateValidator:
    """
    Validates state determinism via hashing.
    
    Core principle:
    state_hash(state) must be deterministic and collision-free for practical use.
    
    Uses SHA256 over canonical JSON representation.
    """
    
    @staticmethod
    def compute_hash(state):
        """
        Compute deterministic hash of state.
        
        Args:
            state: State object
        
        Returns:
            hex digest of canonical JSON representation
        """
        # Convert state to dict representation
        state_dict = state.to_dict()
        
        # Compute hash
        data = json.dumps(state_dict, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    @staticmethod
    def validate_replay(kernel1, kernel2):
        """
        Validate that two kernels produce identical replay.
        
        Args:
            kernel1: First replay kernel
            kernel2: Second replay kernel
        
        Returns:
            True if both produce same state hash, False otherwise
        """
        state1 = kernel1.replay()
        state2 = kernel2.replay()
        
        hash1 = StateValidator.compute_hash(state1)
        hash2 = StateValidator.compute_hash(state2)
        
        return hash1 == hash2

def save_state(state, path):
    """
    Save state to file (for persistence).
    
    Args:
        state: State object
        path: File path (will be created if doesn't exist)
    """
    data = state.to_dict()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_state(path):
    """
    Load state from file.
    
    Args:
        path: File path
        
    Returns:
        State object (or empty State if file missing)
    """
    try:
        with open(path, "r") as f:
            data = json.load(f)
        
        return State.from_dict(data)
    except Exception:
        return State.empty()
