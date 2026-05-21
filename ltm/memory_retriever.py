"""
memory_retriever.py - Retrieve top-K memories from LTM storage layers.
Integrates with memory_router.py and memory_gate.py.
"""

import json
from typing import List, Optional, Tuple
import sys
import os

# Add workspace to path
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

class LTMRetriever:
    """Retrieve memories from episodic and semantic stores."""
    
    def __init__(self, workspace: str = '/home/jason2ykk/.openclaw/workspace'):
        self.workspace = workspace
        self.memory_path = os.path.join(workspace, 'memory', 'memory.jsonl')
        self.episodic_path = os.path.join(workspace, 'memory', 'episodic.jsonl')
        self.semantic_path = os.path.join(workspace, 'memory', 'semantic.jsonl')
        
    def load_memories(self, layers: List[str]) -> List[dict]:
        """
        Load memories from specified layers.
        
        Args:
            layers: 'memory.jsonl', 'episodic', 'semantic', or list thereof
            
        Returns:
            List of memory dictionaries
        """
        memories = []
        
        for layer in layers:
            if layer == 'memory.jsonl':
                memories.extend(self._load_memory_jsonl())
            elif layer == 'episodic':
                memories.extend(self._load_episodic())
            elif layer == 'semantic':
                memories.extend(self._load_semantic())
            elif isinstance(layer, list):
                for l in layer:
                    if l == 'memory.jsonl':
                        memories.extend(self._load_memory_jsonl())
                    elif l == 'episodic':
                        memories.extend(self._load_episodic())
                    elif l == 'semantic':
                        memories.extend(self._load_semantic())
                
        return memories
    
    def retrieve_top_k(self, k: int, layer: Optional[str] = None, 
                      score_threshold: float = 0.0) -> List[dict]:
        """
        Retrieve top-K memories based on layer preference.
        
        Args:
            k: Number of memories to retrieve
            layer: 'memory.jsonl', 'episodic', 'semantic', or None (auto)
            score_threshold: Minimum relevance score (0.0-1.0)
            
        Returns:
            List of top-K memory dictionaries
        """
        if layer is None or layer == 'auto':
            # Default to semantic for factual queries, episodic for temporal
            layer = 'semantic'
            
        # Convert layer to list if needed
        if isinstance(layer, str):
            layers = [layer]
        else:
            layers = layer
        
        memories = self.load_memories(layers)
        
        # Filter by importance threshold (maps to score)
        filtered = [m for m in memories if m.get('importance', 0.0) >= score_threshold]
        
        # Sort by importance descending
        filtered.sort(key=lambda x: x.get('importance', 0.0), reverse=True)
        
        return filtered[:k]
    
    def _load_episodic(self) -> List[dict]:
        """Load episodic memories from JSONL file."""
        try:
            with open(self.episodic_path, 'r') as f:
                memories = []
                for line in f:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return memories
        except FileNotFoundError:
            return []
    
    def _load_semantic(self) -> List[dict]:
        """Load semantic memories from JSONL file."""
        try:
            with open(self.semantic_path, 'r') as f:
                memories = []
                for line in f:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return memories
        except FileNotFoundError:
            return []
    
    def _load_memory_jsonl(self) -> List[dict]:
        """Load memories from main memory.jsonl file."""
        try:
            with open(self.memory_path, 'r') as f:
                memories = []
                for line in f:
                    try:
                        memories.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return memories
        except FileNotFoundError:
            return []

if __name__ == '__main__':
    # Test retrieval
    retriever = LTMRetriever()
    print(f"Loading episodic memories: {len(retriever._load_episodic())}")
    print(f"Loading semantic memories: {len(retriever._load_semantic())}")
