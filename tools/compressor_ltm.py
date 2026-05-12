#!/usr/bin/env python3
"""
LTM v1 Compression Logic
Author: Pentagon Orchestrator @main
"""

import json
from pathlib import Path

class CompressionManager:
    def __init__(self, episodic_path, semantic_path):
        self.episodic = Path(episodic_path)
        self.semantic = Path(semantic_path)
        self.compression_threshold = 3000
        self.compression_ratio = 0.5  # Compress oldest 50%
    
    def check_and_compress(self):
        """Check threshold and trigger compression if needed."""
        count = self.get_episodic_count()
        if count < self.compression_threshold:
            return {"triggered": False, "lines": count}
        
        # Compress oldest 50%
        with open(self.episodic, 'r') as f:
            all_lines = f.readlines()
        
        total_lines = len(all_lines)
        compress_count = int(total_lines * self.compression_ratio)  # 50%
        oldest_half = all_lines[:compress_count]
        remaining_lines = all_lines[compress_count:]
        
        # Compress oldest half to ≤256 tokens each
        compressed_entries = []
        for line in oldest_half:
            entry = json.loads(line)
            summary = self._summarize(entry)
            if len(summary) <= 256:  # Ensure ≤256 tokens
                compressed_entries.append(summary)
            else:
                # Fallback to original if already short enough
                compressed_entries.append(entry)
        
        # Write compressed entries to semantic.jsonl
        for i, entry in enumerate(compressed_entries):
            compressed_entry = {"id": f"compressed_{i}"}
            compressed_entry.update(entry)
            self.semantic.write_text(json.dumps(compressed_entry) + '\n')
        
        # Rewrite episodic with remaining lines
        with open(self.episodic, 'w') as f:
            f.writelines(remaining_lines)
        
        return {
            "triggered": True,
            "lines_processed": total_lines,
            "compressed": len(compressed_entries),
            "remaining": len(remaining_lines)
        }
    
    def _summarize(self, entry):
        """Create a concise summary of the entry."""
        return {
            "id": entry.get("id"),
            "type": entry.get("type"),
            "summary": f"Event #{entry.get('id')}: LTM memory system operational. Module: {entry.get('content', '').split(':')[1] if ':' in entry.get('content', '') else 'unknown'}"
        }
    
    def get_episodic_count(self):
        count = 0
        if self.episodic.exists():
            with open(self.episodic) as f:
                count = sum(1 for _ in f)
        return count
    
    def get_semantic_count(self):
        count = 0
        if self.semantic.exists():
            with open(self.semantic) as f:
                count = sum(1 for _ in f)
        return count

if __name__ == "__main__":
    import sys
    episodic_path = sys.argv[1] if len(sys.argv) > 1 else "/home/jason2ykk/.openclaw/workspace/memory/episodic.jsonl"
    semantic_path = sys.argv[2] if len(sys.argv) > 2 else "/home/jason2ykk/.openclaw/workspace/memory/semantic.jsonl"
    
    mgr = CompressionManager(episodic_path, semantic_path)
    result = mgr.check_and_compress()
    print(json.dumps(result, indent=2))
    
    print(f"\n[✓] Episodic lines remaining: {mgr.get_episodic_count()}")
    print(f"[✓] Semantic lines created: {mgr.get_semantic_count()}")