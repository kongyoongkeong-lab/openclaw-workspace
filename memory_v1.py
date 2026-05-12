#!/usr/bin/env python3
"""
memory_v1.py - Local First Memory System v1

Storage layer:
- Episodic: episodic.jsonl (temporary, compressible)
- Semantic: semantic.jsonl (immutable, vault-like)

Usage:
- memory = init_memory_system("/home/jason2ykk/.openclaw/workspace")
- memory.append_episodic({...})
- memory.append_semantic({...})
- memory.get_episodic_count()
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemorySystem:
    """
    Local memory system for Pentagon agents.
    
    Architecture:
    - Episodic: Temporary, compressible (JSONL)
    - Semantic: Immutable, vault-like (JSONL)
    """
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self._episodic_path = self.workspace / "episodic.jsonl"
        self._semantic_path = self.workspace / "semantic.jsonl"
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure workspace directories exist."""
        self._episodic_path.parent.mkdir(parents=True, exist_ok=True)
        self._semantic_path.parent.mkdir(parents=True, exist_ok=True)
    
    def append_episodic(self, data: Dict[str, Any]) -> bool:
        """Append to episodic memory."""
        try:
            with open(self._episodic_path, "a") as f:
                f.write(json.dumps(data) + "\n")
            return True
        except Exception as e:
            print(f"Error appending episodic: {e}")
            return False
    
    def append_semantic(self, data: Dict[str, Any]) -> bool:
        """Append to semantic memory (immutable)."""
        try:
            with open(self._semantic_path, "a") as f:
                f.write(json.dumps(data) + "\n")
            return True
        except Exception as e:
            print(f"Error appending semantic: {e}")
            return False
    
    def append_agents(self, agent_id: str, data: Dict[str, Any]) -> bool:
        """Append to agent-specific memory."""
        try:
            agent_path = self.workspace / "agents" / agent_id / "memory.jsonl"
            agent_path.parent.mkdir(parents=True, exist_ok=True)
            with open(agent_path, "a") as f:
                f.write(json.dumps(data) + "\n")
            return True
        except Exception as e:
            print(f"Error appending agent memory: {e}")
            return False
    
    def get_episodic_count(self) -> int:
        """Get episodic memory line count."""
        if not self._episodic_path.exists():
            return 0
        with open(self._episodic_path) as f:
            return sum(1 for _ in f)
    
    def get_semantic_count(self) -> int:
        """Get semantic memory line count."""
        if not self._semantic_path.exists():
            return 0
        with open(self._semantic_path) as f:
            return sum(1 for _ in f)
    
    def get_latest_episodic(self, limit: int = 5) -> List[Dict]:
        """Get latest episodic entries."""
        if not self._episodic_path.exists():
            return []
        
        entries = []
        with open(self._episodic_path) as f:
            lines = f.readlines()[-limit:]
            for line in reversed(lines):
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    pass
        return entries
    
    def search_episodic(self, query: str) -> List[Dict]:
        """Search episodic memory for query keywords."""
        if not self._episodic_path.exists():
            return []
        
        results = []
        with open(self._episodic_path) as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    entry_str = json.dumps(entry).lower()
                    if query.lower() in entry_str:
                        results.append(entry)
                except json.JSONDecodeError:
                    continue
        return results


def init_memory_system(workspace: Optional[str] = None) -> MemorySystem:
    """Initialize memory system."""
    return MemorySystem(workspace=workspace)


# Test
if __name__ == "__main__":
    memory = init_memory_system("/home/jason2ykk/.openclaw/workspace")
    
    # Example usage
    print("🧠 Pentagon Memory System Initialized")
    print(f"Episodic lines: {memory.get_episodic_count()}")
    print(f"Semantic lines: {memory.get_semantic_count()}")
    
    # Example append
    memory.append_episodic({
        "event": "test",
        "timestamp": time.time(),
        "data": "test data",
    })
    
    print(f"After test - Episodic lines: {memory.get_episodic_count()}")
