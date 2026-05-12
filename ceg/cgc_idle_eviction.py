#!/usr/bin/env python3
"""
Cognitive Garbage Collector (CGC) - Idle Context Auto-Eviction
Priority: CRITICAL (99% context usage)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# ========= CONFIGURATION =========
STALE_CYCLE_THRESHOLD = 30  # ~5 minutes at typical runtime
AUTO_EVICT_IDLE = True
MAX_GOVERNANCE_OVERHEAD = 0.20  # 20%
MIN_CONTEXT_HEADROOM = 0.10  # 10% minimum

# ========= EVICTION PRIORITY =========
# Priority 0 (Highest): Must delete first
PRIORITY_0 = [
    "telemetry_logs",
    "old_repair_events",
    "completed_task_outputs",
    "verbose_tool_logs",
    "stale_queue_metrics",
    "dead_agent_outputs",
    "unused_retrievals",
    "ended_dependency_chains",
]

# Priority 1: Low priority but important
PRIORITY_1 = [
    "agent_activity_logs",
    "session_metadata",
    "minor_queue_updates",
]

# Priority 2: NEVER delete
PRIORITY_2 = [
    "governance_state",
    "active_dependency_chain",
    "unresolved_failures",
    "safety_constraints",
    "runtime_state",
]

# ========= 4-FACTOR EVICTION SCORE =========
def calculate_eviction_score(
    slot: Dict,
    age_factor: float = 0.4,
    irrelevance_factor: float = 0.3,
    duplication_factor: float = 0.2,
    verbosity_factor: float = 0.1,
) -> float:
    """
    Calculate eviction score for a context slot.
    
    Factors:
    - staleness: how long unreferenced (age_factor)
    - irrelevance: no task affinity (irrelevance_factor)
    - duplication: duplicate content already elsewhere (duplication_factor)
    - verbosity: verbose logs over compact data (verbosity_factor)
    """
    
    # Staleness: cycles since last reference
    last_ref = slot.get("last_reference_cycle", 0)
    current_cycle = datetime.now().timestamp() / 60  # Convert to minutes
    stale_minutes = current_cycle - last_ref
    
    if stale_minutes <= STALE_CYCLE_THRESHOLD:
        staleness = 0  # Not stale
    else:
        # Normalize to 0-1 scale (older = higher score)
        staleness = min(1.0, stale_minutes / STALE_CYCLE_THRESHOLD)
    
    # Irrelevance: check task affinity
    task_affinity = slot.get("task_affinity", 0)
    irrelevance = 1 - task_affinity  # No affinity = high irrelevance
    
    # Duplication: check if content already in other slots
    duplication = slot.get("duplication_score", 0)
    
    # Verbosity: token density
    tokens = slot.get("token_count", 0)
    if tokens > 0:
        verbosity = min(1.0, tokens / 4000)  # 4k tokens = max verbosity
    else:
        verbosity = 0
    
    # Weighted score
    score = (
        staleness * age_factor +
        irrelevance * irrelevance_factor +
        duplication * duplication_factor +
        verbosity * verbosity_factor
    )
    
    return score

# ========= SLOT RISK CLASSIFICATION =========
def classify_slot_risk(slot: Dict) -> str:
    """Classify slot by risk of deletion."""
    
    token_count = slot.get("token_count", 0)
    last_ref = slot.get("last_reference_cycle", 0)
    category = slot.get("category", "unknown")
    
    # Critical categories - never delete
    if category in PRIORITY_2:
        return "CRITICAL - NEVER DELETE"
    
    # Stale tokens
    stale_minutes = last_ref if last_ref == 0 else (
        (datetime.now().timestamp() / 60) - last_ref
    )
    is_stale = stale_minutes > STALE_CYCLE_THRESHOLD
    
    # Small tokens (easier to delete)
    is_small = token_count < 100
    
    if is_stale and is_small:
        return "HIGH RISK - SAFE TO DELETE"
    elif is_stale:
        return "MEDIUM RISK - REVIEW BEFORE DELETE"
    else:
        return "LOW RISK - KEEP FOR NOW"

# ========= AUTO-EVICTOR =========
class IdleContextEvictor:
    def __init__(self, context_store_path: str = "/home/jason2ykk/.openclaw/workspace/memory/2026-05-10.md"):
        self.context_store_path = Path(context_store_path)
        self.context_slots = self._parse_context_slots()
        
    def _parse_context_slots(self) -> List[Dict]:
        """Parse context from episodic memory file."""
        slots = []
        
        # Simple parsing - extract context blocks
        try:
            content = self.context_store_path.read_text()
            
            # Look for memory entries
            import re
            # Extract timestamped blocks
            pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
            matches = re.finditer(pattern, content)
            
            # Create slot metadata from file
            for match in matches:
                slots.append({
                    "timestamp": match.group(),
                    "category": "episodic_memory",
                    "token_count": len(match.group()),
                    "last_reference_cycle": match.start() / 60,
                    "task_affinity": 0.5,  # Moderate affinity for memory
                    "duplication_score": 0.1,
                    "is_stale": False,
                    "eviction_score": 0.0,
                })
        except Exception as e:
            print(f"Error parsing context slots: {e}")
        
        return slots
    
    def scan_for_idle_context(self) -> List[Dict]:
        """Scan context for idle/unreferenced slots."""
        idle_slots = []
        
        current_time = datetime.now().timestamp() / 60
        
        for slot in self.context_slots:
            # Skip critical slots
            if slot.get("category", "") in ["governance_state", "runtime_state"]:
                continue
            
            last_ref = slot.get("last_reference_cycle", current_time)
            stale_minutes = current_time - last_ref
            
            is_stale = stale_minutes > STALE_CYCLE_THRESHOLD
            
            # Update slot metadata
            slot["is_stale"] = is_stale
            slot["current_cycle"] = current_time
            
            # Calculate eviction score
            if is_stale:
                slot["eviction_score"] = calculate_eviction_score(slot)
            else:
                slot["eviction_score"] = 0.0
            
            # Classify risk
            slot["risk_class"] = classify_slot_risk(slot)
            
            # Check if idle
            if is_stale:
                idle_slots.append(slot)
        
        # Sort by eviction score (highest first)
        idle_slots.sort(key=lambda x: x.get("eviction_score", 0), reverse=True)
        
        return idle_slots
    
    def evict_slots(self, idle_slots: List[Dict], max_eviction_limit: int = 5000) -> List[Dict]:
        """Evict idle context slots."""
        evicted = []
        
        for slot in idle_slots:
            risk = slot.get("risk_class", "")
            
            # Never delete PRIORITY_2 content
            if "CRITICAL" in risk:
                continue
            
            # Check if within token limit
            if slot.get("token_count", 0) + sum(s.get("token_count", 0) for s in evicted) > max_eviction_limit:
                break
            
            # Evict this slot
            evicted.append(slot)
            
            # Log eviction
            print(f"🗑️  EVICTED: {slot['timestamp']} - {risk} - {slot['token_count']} tokens")
        
        return evicted
    
    def run_auto_eviction(self) -> Dict:
        """Run automatic eviction cycle."""
        print("🔍 Scanning for idle context...")
        
        idle_slots = self.scan_for_idle_context()
        evicted = self.evict_slots(idle_slots)
        
        return {
            "total_idle_slots": len(idle_slots),
            "evicted_count": len(evicted),
            "total_evicted_tokens": sum(s.get("token_count", 0) for s in evicted),
            "evicted_slots": evicted,
        }

# ========= MAIN EXECUTION =========
if __name__ == "__main__":
    evictor = IdleContextEvictor()
    
    # Run auto-eviction
    result = evictor.run_auto_eviction()
    
    print(f"\n✅ Auto-eviction complete")
    print(f"  Idle slots found: {result['total_idle_slots']}")
    print(f"  Slots evicted: {result['evicted_count']}")
    print(f"  Tokens reclaimed: {result['total_evicted_tokens']}")