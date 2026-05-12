"""
ltm_pipeline.py - Long-Term Memory Pipeline Orchestrator

This module orchestrates the LTM workflow:
1. Gate: Check token budget
2. Retrieve: Fetch top-K relevant memories
3. Inject: Add new memory (with compression if needed)
4. Store: Persist to episodic/semantic stores

Usage:
    python3 ltm_pipeline.py --inject --query "What was discussed yesterday?"
    python3 ltm_pipeline.py --retrieve --k 5
"""

import json
import argparse
import sys
import os
from datetime import datetime
from typing import List, Tuple, Optional

# Add workspace to path
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

from ltm.memory_gate import MemoryGate
from ltm.memory_retriever import LTMRetriever

# Configuration
MAX_TOKENS = 8000
COMPRESSION_THRESHOLD = 3000  # Lines to compress
WORKSPACE = '/home/jason2ykk/.openclaw/workspace'

class LTMPipeline:
    """Orchestrates the full LTM memory pipeline."""
    
    def __init__(self, workspace: str = WORKSPACE):
        self.workspace = workspace
        self.gate = MemoryGate(max_tokens=MAX_TOKENS)
        self.retriever = LTMRetriever(workspace=workspace)
        
        # Memory paths
        self.episodic_path = os.path.join(workspace, 'memory', 'episodic.jsonl')
        self.semantic_path = os.path.join(workspace, 'memory', 'semantic.jsonl')
        self.compressed_path = os.path.join(workspace, 'memory', 'compressed.jsonl')
        
    def inject_memory(self, memory: dict, 
                    auto_compress: bool = False,
                    force: bool = False) -> bool:
        """
        Inject new memory into appropriate store.
        
        Args:
            memory: Dictionary to store
            auto_compress: Apply compression before storing
            force: Bypass compression check
            
        Returns:
            True if successful
        """
        # Check if compression needed
        if not auto_compress and self._needs_compression(memory):
            if not force:
                return False  # Compression not applied
            memory, _ = self._compress_memory(memory)
            
        # Store to appropriate layer
        layer = self._determine_layer(memory.get('type', 'episodic'))
        
        with open(self._get_path(layer), 'a') as f:
            f.write(json.dumps(memory) + '\n')
            
        return True
    
    def retrieve(self, k: int = 5, 
                layer: Optional[str] = None,
                score_threshold: float = 0.5) -> List[dict]:
        """Retrieve top-K memories."""
        memories = self.retriever.retrieve_top_k(k, layer=layer, 
                                                  score_threshold=score_threshold)
        # Handle list format if needed
        if isinstance(memories, list) and len(memories) > 0 and isinstance(memories[0], list):
            memories = [m for m in memories for item in m if isinstance(item, dict)]
        return memories
    
    def check_budget(self) -> bool:
        """Check if memory set fits within token budget."""
        return self.gate.check_budget(self._load_all_memories())
    
    def _needs_compression(self, memory: dict) -> bool:
        """Check if memory exceeds compression threshold."""
        content = memory.get('content', '')
        lines = len(content.split('\n'))
        return lines > COMPRESSION_THRESHOLD
    
    def _compress_memory(self, memory: dict) -> Tuple[dict, int]:
        """
        Compress memory content to reduce storage size.
        
        Returns:
            Tuple of (compressed_memory, original_line_count)
        """
        content = memory['content']
        lines = content.split('\n')
        original_lines = len(lines)
        
        # Simple compression: group similar lines
        if original_lines > COMPRESSION_THRESHOLD:
            # Group lines into chunks
            chunks = []
            current_chunk = []
            for line in lines:
                current_chunk.append(line)
                if len(current_chunk) >= 10:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
            if current_chunk:
                chunks.append('\n'.join(current_chunk))
            
            # Store as meta-structure
            compressed_content = {
                'type': 'compressed',
                'chunks': chunks,
                'original_lines': original_lines
            }
            
            memory['content'] = json.dumps(compressed_content)
            
        return memory, original_lines
    
    def _determine_layer(self, memory_type: str) -> str:
        """Determine whether to store in episodic or semantic layer."""
        if memory_type == 'semantic' or memory.get('importance') == 'high':
            return 'semantic'
        return 'episodic'
    
    def _get_path(self, layer: str) -> str:
        """Get file path for specified layer."""
        if layer == 'semantic':
            return self.semantic_path
        elif layer == 'compressed':
            return self.compressed_path
        return self.episodic_path
    
    def _load_all_memories(self) -> List[dict]:
        """Load all memories from all layers."""
        memories = []
        
        # Load episodic
        if os.path.exists(self.episodic_path):
            with open(self.episodic_path, 'r') as f:
                for line in f:
                    try:
                        episodic_data = json.loads(line)
                        # Handle list format
                        if isinstance(episodic_data, list):
                            for item in episodic_data:
                                if isinstance(item, dict):
                                    memories.append(item)
                        elif isinstance(episodic_data, dict):
                            memories.append(episodic_data)
                    except json.JSONDecodeError:
                        continue
        
        # Load semantic
        if os.path.exists(self.semantic_path):
            with open(self.semantic_path, 'r') as f:
                for line in f:
                    try:
                        semantic_data = json.loads(line)
                        # Handle list format
                        if isinstance(semantic_data, list):
                            for item in semantic_data:
                                if isinstance(item, dict):
                                    memories.append(item)
                        elif isinstance(semantic_data, dict):
                            memories.append(semantic_data)
                    except json.JSONDecodeError:
                        continue
                        
        # Load compressed
        if os.path.exists(self.compressed_path):
            with open(self.compressed_path, 'r') as f:
                for line in f:
                    try:
                        compressed = json.loads(line)
                        if isinstance(compressed, dict) and 'chunks' in compressed:
                            # Expand compressed content
                            chunks = compressed['chunks']
                            memory = {
                                'content': '\n'.join(chunks),
                                'type': 'compressed_expanded',
                                'original_lines': compressed.get('original_lines', 0)
                            }
                            memories.append(memory)
                    except json.JSONDecodeError:
                        continue
                        
        return memories
    
    def analyze(self, workspace: str = WORKSPACE) -> dict:
        """
        Analyze current memory state.
        
        Returns:
            Dictionary with memory statistics
        """
        memories = self._load_all_memories()
        
        total_tokens = sum(len(m.get('content', '')) for m in memories)
        layer_counts = {'episodic': 0, 'semantic': 0, 'compressed': 0}
        
        # Count by layer
        for m in memories:
            content = m.get('content', '')
            try:
                if isinstance(content, dict):
                    # Compressed entry
                    if 'chunks' in content:
                        layer_counts['compressed'] += 1
                    else:
                        layer_counts['episodic'] += 1
                else:
                    layer_counts['episodic'] += 1
            except:
                layer_counts['episodic'] += 1
        
        return {
            'total_memories': len(memories),
            'total_tokens': total_tokens,
            'layer_counts': layer_counts,
            'in_budget': self.gate.check_budget(memories)
        }


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description='LT MemPy Pipeline')
    parser.add_argument('--inject', action='store_true', 
                       help='Inject new memory')
    parser.add_argument('--retrieve', action='store_true',
                       help='Retrieve top-K memories')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze memory state')
    parser.add_argument('--k', type=int, default=5,
                       help='Number of memories to retrieve')
    parser.add_argument('--query', type=str,
                       help='Query string for retrieval')
    parser.add_argument('--memory', type=str,
                       help='JSON string to inject')
    
    args = parser.parse_args()
    
    pipeline = LTMPipeline()
    
    if args.analyze:
        stats = pipeline.analyze()
        print("\n=== Memory Analysis ===")
        print(f"Total memories: {stats['total_memories']}")
        print(f"Total tokens: {stats['total_tokens']}")
        print(f"In budget: {stats['in_budget']}")
        print(f"Layer counts: {stats['layer_counts']}")
        
    elif args.retrieve:
        memories = pipeline.retrieve(k=args.k)
        print(f"\n=== Retrieved {len(memories)} Memories ===")
        for i, mem in enumerate(memories, 1):
            print(f"\n[{i}] {mem.get('id', 'no-id')}")
            print(f"    Content: {mem.get('content', '')[:200]}...")
            print(f"    Score: {mem.get('score', 0.0)}")
            
    elif args.inject:
        memory = json.loads(args.memory)
        if pipeline.inject_memory(memory):
            print("✓ Memory injected successfully")
        else:
            print("✗ Memory injection failed (compression required)")
            
    else:
        print("Use --help for usage options")
        print("\nExample:")
        print('  python3 ltm_pipeline.py --retrieve --k 5')


if __name__ == '__main__':
    main()
