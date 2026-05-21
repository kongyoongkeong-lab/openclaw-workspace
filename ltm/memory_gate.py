"""
memory_gate.py - Token budget enforcement for LTM memory management.
Ensures memory systems stay within configurable token limits.
"""

import json
from typing import List, Tuple, Optional
import sys
import os

# Add workspace to path
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

class MemoryGate:
    """Enforce token budget constraints on memory systems."""
    
    TOKEN_PER_MEMORY = 400  # Average tokens per memory entry
    
    def __init__(self, max_tokens: int = 8000):
        """
        Initialize gate with token budget.
        
        Args:
            max_tokens: Maximum total tokens allowed (default: 8000)
        """
        self.max_tokens = max_tokens
        
    def get_token_count(self, memories: List[dict]) -> int:
        """Calculate total tokens in memory set."""
        return sum(len(m.get('content', '')) for m in memories)
    
    def prune_excess(self, memories: List[dict], 
                    keep_ratio: float = 0.7) -> Tuple[List[dict], int]:
        """
        Prune memories to fit token budget, keeping highest-scoring.
        
        Args:
            memories: List of memory dictionaries
            keep_ratio: Fraction of memories to retain (default: 0.7)
            
        Returns:
            Tuple of (pruned_memories, tokens_pruned)
        """
        total_tokens = self.get_token_count(memories)
        tokens_available = self.max_tokens - total_tokens
        
        if tokens_available <= 0:
            return memories[:], total_tokens
        
        # Sort by score descending
        sorted_memories = sorted(
            memories, 
            key=lambda m: m.get('score', 0.0), 
            reverse=True
        )
        
        # Calculate how many to keep
        target_count = int(len(sorted_memories) * keep_ratio)
        
        if target_count >= len(sorted_memories):
            return memories[:], total_tokens
        
        memories_to_remove = sorted_memories[target_count:]
        tokens_pruned = self.get_token_count(memories_to_remove)
        
        return sorted_memories[:target_count], tokens_pruned
    
    def check_budget(self, memories: List[dict]) -> bool:
        """Check if memory set fits within budget."""
        total_tokens = self.get_token_count(memories)
        return total_tokens <= self.max_tokens
    
    def optimize_for_query(self, query: str, 
                          k: int = 5, 
                          layers: List[str] = None) -> List[dict]:
        """
        Select memories that best match query while respecting budget.
        
        Args:
            query: User query string
            k: Number of memories to select
            layers: Preferred layers (default: ['semantic', 'episodic'])
            
        Returns:
            Optimized memory list
        """
        if layers is None:
            layers = ['semantic', 'episodic']
        
        # Load memories
        retriever = LTMRetriever()
        all_memories = retriever.load_memories(layers)
        
        # Prune to budget if needed
        if not self.check_budget(all_memories):
            all_memories, _ = self.prune_excess(all_memories, keep_ratio=0.9)
        
        # Select top-K by score
        return retriever.retrieve_top_k(k, layer='auto', 
                                       score_threshold=0.5)

# Convenience functions for memory_router.py
def retrieve_top_k_memories(k: int, 
                           workspace: str = '/home/jason2ykk/.openclaw/workspace',
                           layers: List[str] = None,
                           score_threshold: float = 0.5) -> List[dict]:
    """Public API: Retrieve top-K memories."""
    retriever = LTMRetriever(workspace=workspace)
    return retriever.retrieve_top_k(k, layer='auto', score_threshold=score_threshold)

def prune_memory_set(memories: List[dict], max_tokens: int = 8000,
                    keep_ratio: float = 0.7) -> Tuple[List[dict], int]:
    """Public API: Prune memory set to fit budget."""
    gate = MemoryGate(max_tokens=max_tokens)
    return gate.prune_excess(memories, keep_ratio=keep_ratio)

if __name__ == '__main__':
    # Test gate functionality
    gate = MemoryGate()
    print(f"Token budget: {gate.max_tokens} tokens")
    
    # Create test memories
    test_memories = [
        {'content': 'Test memory 1', 'score': 0.9},
        {'content': 'Test memory 2', 'score': 0.8},
        {'content': 'Test memory 3', 'score': 0.7},
    ]
    
    pruned, pruned_tokens = gate.prune_excess(test_memories)
    print(f"Pruned tokens: {pruned_tokens}")
    print(f"Pruned memories: {len(pruned)}")
