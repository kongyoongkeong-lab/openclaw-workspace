# Idle Context Occupancy Detector
"""
Detect and flag wasted context slots.

Targets:
- Tokens not referenced in >N turns
- Governance tokens long-residing unused
- Retrievals never cited
- Telemetry zombie data

Formula: Idle% = idle_context_slots / total_context_capacity
Alert: Idle% > 30% warning, > 50% critical
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

MEMORY_DIR = Path(__file__).parent / "memory"
EPISODIC_FILE = MEMORY_DIR / "episodic.jsonl"

# Configuration
DEFAULT_REFERENCE_WINDOW = 5  # turns
IDLE_THRESHOLD_WARNING = 30   # percent
IDLE_THRESHOLD_CRITICAL = 50  # percent


@dataclass
class ContextSlot:
    """Represents a single context slot."""
    slot_id: str
    content_type: str  # memory, retrieval, telemetry, etc.
    content_summary: str
    last_referenced: int  # turn number
    turn_count_total: int
    cited_count: int = 0
    is_governance_token: bool = False


@dataclass
class IdleContextReport:
    """Report on idle context occupancy."""
    total_slots: int = 0
    idle_slots: int = 0
    idle_percent: float = 0.0
    warning_slots: List[ContextSlot] = field(default_factory=list)
    critical_slots: List[ContextSlot] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


def load_context_slots() -> List[ContextSlot]:
    """Load all context slots from memory history."""
    slots = []
    try:
        with open(EPISODIC_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)
                
                # Skip metadata-only entries
                if entry.get('type') == 'metadata' and not entry.get('content'):
                    continue
                
                slot = ContextSlot(
                    slot_id=f"{entry.get('type', 'unknown')}_{entry.get('id', entry.get('timestamp', ''))}",
                    content_type=entry.get('type', 'unknown'),
                    content_summary=entry.get('summary', entry.get('text', ''))[:200],
                    last_referenced=entry.get('referenced_at', 0),
                    turn_count_total=len(slots) + 1,
                    cited_count=entry.get('cited_count', 0),
                    is_governance_token=entry.get('is_governance', False)
                )
                slots.append(slot)
    except FileNotFoundError:
        print(f"Episodic file not found: {EPISODIC_FILE}")
    
    return slots


def analyze_idle_context(slots: List[ContextSlot], current_turn: int) -> IdleContextReport:
    """Analyze context slots for idle/dead content."""
    if not slots:
        return IdleContextReport()
    
    report = IdleContextReport()
    
    for slot in slots:
        report.total_slots += 1
        
        # Determine if slot is idle
        turns_since_reference = current_turn - slot.last_referenced
        
        # Check if slot has never been cited
        never_cited = slot.cited_count == 0
        
        # Mark as idle if:
        # 1. Never cited AND old (more than reference window)
        # 2. Last referenced > reference window turns ago
        # 3. Governance token unused for long period
        is_idle = (turns_since_reference > DEFAULT_REFERENCE_WINDOW and 
                   (never_cited or (slot.is_governance_token and turns_since_reference > 3)))
        
        if is_idle:
            report.idle_slots += 1
            
            # Categorize by severity
            if turns_since_reference > DEFAULT_REFERENCE_WINDOW * 3:
                report.critical_slots.append(slot)
                report.recommendations.append(
                    f"CRITICAL: Delete {slot.content_type} '{slot.slot_id[:50]}...': "
                    f"unreferenced for {turns_since_reference} turns"
                )
            else:
                report.warning_slots.append(slot)
                report.recommendations.append(
                    f"WARNING: Consider compressing {slot.content_type} '{slot.slot_id[:50]}...': "
                    f"unreferenced for {turns_since_reference} turns"
                )
    
    report.idle_percent = (report.idle_slots / report.total_slots * 100) if report.total_slots > 0 else 0.0
    return report


def generate_eviction_plan(report: IdleContextReport) -> List[Tuple[str, str]]:
    """Generate plan for evicting idle context."""
    plan = []
    for slot in report.critical_slots + report.warning_slots:
        action = "COMPRESS" if slot.content_type == "telemetry" else "EVICT"
        plan.append((slot.slot_id, f"{action}: {slot.content_type}"))
    return plan


def run_idle_context_analysis(current_turn: int = 10) -> IdleContextReport:
    """Run idle context occupancy analysis."""
    print(f"🔍 Analyzing idle context (turn {current_turn})...")
    slots = load_context_slots()
    print(f"  Loaded {len(slots)} context slots")
    
    report = analyze_idle_context(slots, current_turn)
    
    if report.idle_percent > 0:
        print(f"  📊 Idle Context: {report.idle_percent:.1f}% ({report.idle_slots}/{report.total_slots} slots)")
        
        if report.idle_percent >= IDLE_THRESHOLD_CRITICAL:
            print(f"  🚨 CRITICAL: Idle context exceeds {IDLE_THRESHOLD_CRITICAL}% threshold!")
        elif report.idle_percent >= IDLE_THRESHOLD_WARNING:
            print(f"  ⚠️  WARNING: Idle context exceeds {IDLE_THRESHOLD_WARNING}% threshold!")
        
        for rec in report.recommendations[:5]:  # Show top 5 recommendations
            print(f"    - {rec}")
    
    return report


if __name__ == "__main__":
    # Demo: Run analysis
    report = run_idle_context_analysis(current_turn=10)
    print(f"\n📋 Report: {report.idle_percent:.1f}% idle")
    plan = generate_eviction_plan(report)
    print(f"Eviction plan: {len(plan)} items")
