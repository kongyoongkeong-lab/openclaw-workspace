#!/usr/bin/env python3
"""
ltm_pipeline.py - Long-Term Memory Pipeline Orchestrator (v1)

CRITICAL: Full end-to-end pipeline for memory retrieval, gating, and storage
"""

import sys
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Optional

# Add workspace to path
sys.path.insert(0, os.path.dirname(__file__))

from memory_store import write_entry, write_entries
from memory_retriever import retrieve_top_k
from memory_gate import memory_gate
from context_builder import build_context

# Pipeline configuration
MAX_TOKENS = 8000
COMPRESSION_THRESHOLD = 3000
COMPRESSED_TOKEN_RATIO = 0.5

class Pipeline:
    """LTM Pipeline Orchestrator"""
    
    def __init__(self):
        self.stats = {
            "entries_processed": 0,
            "entries_written": 0,
            "errors": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        print(f"[PIPELINE] v1 Initialized at {self.stats['timestamp']}")
    
    def process(self, user_input: str) -> Optional[Dict]:
        """
        Full pipeline: Retrieve → Gate → Build → Store
        Returns processed context or None on error
        """
        print(f"\n[PIPELINE] Processing input: '{user_input[:50]}...'")
        
        try:
            # Step 1: RETRIEVE
            print("[1/4] RETRIEVE...")
            retrieved = retrieve_top_k(user_input, k=50)
            print(f"       Found {len(retrieved)} relevant entries")
            
            if not retrieved:
                print("[1/4] No relevant memory found")
                return {"status": "no_memory", "context": user_input}
            
            # Step 2: GATE
            print("[2/4] GATE...")
            gated = memory_gate(retrieved, max_tokens=MAX_TOKENS)
            print(f"       Gated to {len(gated)} entries")
            
            # Step 3: BUILD CONTEXT
            print("[3/4] BUILD CONTEXT...")
            context = build_context(user_input, gated)
            tokens = len(context) // 4  # Rough estimate
            print(f"       Context size: ~{tokens} tokens")
            
            if tokens > MAX_TOKENS:
                print("[3/4] ERROR: Context exceeds token budget")
                self.stats["errors"] += 1
                return {"status": "error", "message": "Token budget exceeded"}
            
            # Step 4: STORE
            print("[4/4] STORE...")
            entry = {
                "timestamp": datetime.utcnow().isoformat() + "+08:00",
                "type": "pipeline_output",
                "text": f"Pipeline processed: '{user_input[:100]}...' → {len(gated)}/50 entries gated, {len(context)} chars context",
                "author": "@main",
                "user_input": user_input,
                "gated_count": len(gated),
                "context_size": len(context)
            }
            
            written = write_entry(entry)
            self.stats["entries_written"] += 1
            
            if written:
                print(f"       Entry written successfully")
            else:
                print("[4/4] ERROR: Failed to write entry")
                self.stats["errors"] += 1
            
            return {"status": "success", "context": context, "stats": self.stats}
            
        except Exception as e:
            print(f"[PIPELINE] ERROR: {e}")
            self.stats["errors"] += 1
            return {"status": "error", "message": str(e)}
    
    def run_test(self):
        """Run end-to-end test with sample input"""
        test_input = "Deploy production build to Azure with Docker Compose"
        result = self.process(test_input)
        print(f"\n[PIPELINE] Test complete: {result['status']}")
        return result


if __name__ == "__main__":
    pipeline = Pipeline()
    result = pipeline.run_test()
    
    print(f"\n=== FINAL STATS ===")
    print(f"Entries processed: {pipeline.stats['entries_processed']}")
    print(f"Entries written: {pipeline.stats['entries_written']}")
    print(f"Errors: {pipeline.stats['errors']}")
