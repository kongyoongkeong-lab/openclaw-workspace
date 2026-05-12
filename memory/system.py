#!/usr/bin/env python3
"""
Memory System - Core Runtime Integration
================================================
This module provides memory injection hooks for OpenClaw agents.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Memory Paths
MEMORY_BASE = "/home/jason2ykk/.openclaw/workspace/memory"
EPISODIC_PATH = os.path.join(MEMORY_BASE, "episodic.jsonl")
SEMANTIC_PATH = os.path.join(MEMORY_BASE, "semantic.jsonl")
COMPRESSED_PATH = os.path.join(MEMORY_BASE, "compressed.jsonl")
AGENT_LOGS_PATH = os.path.join(MEMORY_BASE, "agents")


def inject_memory_into_prompt(
    agent_id: str,
    prompt: str,
    context: Optional[str] = None
) -> str:
    """
    Inject memory into prompt before LLM call.
    
    Usage:
        enhanced_prompt = inject_memory_into_prompt("@ops", "What files should I create?")
    """
    from memory_router import MemoryRouter, MemoryEntry
    router = MemoryRouter()
    return router.inject_memory_into_prompt(agent_id, prompt, context)


def get_memory_state(agent_id: str) -> Dict[str, Any]:
    """Get current memory state for agent."""
    from memory_router import MemoryRouter
    router = MemoryRouter()
    return router.get_memory_summary(agent_id)


def check_compression_health() -> Dict[str, Any]:
    """Check memory compression health."""
    episodic = []
    semantic = []
    compressed = []
    
    try:
        with open(EPISODIC_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    episodic.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass
    
    try:
        with open(SEMANTIC_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    semantic.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass
    
    try:
        with open(COMPRESSED_PATH, 'r') as f:
            for line in f:
                if line.strip():
                    compressed.append(json.loads(line.strip()))
    except FileNotFoundError:
        pass
    
    return {
        "episodic_count": len(episodic),
        "semantic_count": len(semantic),
        "compressed_count": len(compressed),
        "compression_threshold": 3000,
        "needs_compression": len(episodic) + len(semantic) > 3000
    }


def get_agent_memory(agent_id: str, max_events: int = 10) -> List[Dict[str, Any]]:
    """Get recent memory events for agent."""
    from memory_router import MemoryRouter
    router = MemoryRouter()
    memory = router.get_relevant_memory(agent_id, limit=max_events)
    
    result = []
    for section in [memory.get("episodic_memory"), memory.get("semantic_memory")]:
        for event in section:
            result.append(event)
    
    return result[:max_events]


if __name__ == "__main__":
    print("=== Memory System Runtime ===\n")
    
    # Test memory injection
    prompt = "Create a Python file for data processing."
    enhanced = inject_memory_into_prompt("@ops", prompt, "project_setup")
    print(f"Original prompt: {prompt}")
    print(f"Enhanced prompt:\n{enhanced[:500]}...\n")
    
    # Check health
    health = check_compression_health()
    print(f"Memory Health: {health}")