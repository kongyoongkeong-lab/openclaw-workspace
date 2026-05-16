#!/usr/bin/env python3
"""
Phase 6.2 — Deterministic Scheduling Configuration
Context Pruning Scheduler for OpenClaw (H1-Compliant)

Objective: Enforce predictable, repeatable pruning cycles
Strategy: Sliding window retention + TRI-based vector prioritization

⚠️ H1 Constraint: Passive telemetry only. No governance actions triggered.
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import hashlib

# Add tools directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ------------------------------------------------------
# PHASE 6.1 IMPORT (RPR Stabilization)
# ------------------------------------------------------
from phase6_1_rpr_config import (
    ContextPruningConfig,
    DeterministicPruner,
    PassiveTelemetryHook,
    H1_METRICS,
)

# ------------------------------------------------------
# SCHEDULER CONFIGURATION
# ------------------------------------------------------
class DeterministicScheduler:
    """
    H1-compliant deterministic pruning scheduler.
    
    Ensures pruning cycles are predictable and repeatable.
    Maintains strict order: last_access_time DESC → TRI score DESC → relevance DESC
    
    All scheduling actions are passive telemetry only.
    No governance actions triggered automatically.
    """
    
    # 1. SCHEDULING INTERVALS
    PRUNING_CYCLE_INTERVAL_MINUTES: int = 60  # Run pruning every 60 minutes
    SCHEDULER_ACTIVE_HOURS: list[int] = list(range(6, 23))  # 06:00-23:00 only
    
    # 2. SLIDING WINDOW CONFIG
    WINDOW_SIZE: int = 50  # Number of task outputs retained
    WINDOW_RETENTION_POLICY: str = "tri_weighted"  # "fifo" | "tri_weighted" | "relevance_weighted"
    
    # 3. PRIORITY ORDERING (Deterministic)
    PRUNING_KEY_ORDER: list[tuple[str, bool]] = [
        ("last_access_time", True),  # DESC (most recent first)
        ("tri_score", True),         # DESC (higher TRI retained)
        ("relevance", True),         # DESC (more relevant retained)
    ]
    
    # 4. CACHE EFFICIENCY
    CACHE_HIT_THRESHOLD: float = 0.7  # Above this: reuse without re-query
    CACHE_MISS_PENALTY: float = 0.5   # Below this: prune older vectors
    
    # 5. SCHEDULER STATE
    last_pruning_cycle: Optional[datetime] = None
    consecutive_safe_cycles: int = 0
    
    # 6. TELEMETRY AGGREGATION
    telemetry_buffer_size: int = 10
    telemetry_buffer: list[dict] = []
    
    def __init__(self, config: ContextPruningConfig):
        self.config = config
        self.pruner = DeterministicPruner(config)
        self.telemetry = PassiveTelemetryHook(config)
        
    def check_scheduler_cycle(self) -> bool:
        """
        Check if a pruning cycle should be triggered.
        
        Returns True if pruning cycle should run.
        Enforces H1 passive telemetry only.
        """
        
        now = datetime.now()
        
        # Check active hours
        if now.hour not in self.SCHEDULER_ACTIVE_HOURS:
            return False
        
        # Check interval
        if self.last_pruning_cycle:
            interval = (now - self.last_pruning_cycle).total_seconds() / 60
            if interval < self.PRUNING_CYCLE_INTERVAL_MINUTES:
                return False
        
        return True
    
    def execute_pruning_cycle(self) -> dict:
        """
        Execute a deterministic pruning cycle.
        
        Returns telemetry summary.
        """
        
        now = datetime.now()
        
        # Get active vectors
        active_vectors = self.config.get_active_vectors(now)
        
        # Compute pruning priorities
        prioritized = []
        for vector in active_vectors:
            priority_score, sort_key = self.pruner.compute_pruning_priority(vector, now)
            prioritized.append((vector, priority_score, sort_key))
        
        # Sort by priority (lower = higher pruning risk)
        prioritized.sort(key=lambda x: x[1])
        
        # Apply pruning (passive telemetry only)
        vectors_to_prune = prioritized[:self.config.SLIDING_WINDOW_SIZE]
        vectors_pruned = [v for v in vectors_to_prune if self.pruner.should_prune_vector(v, now)]
        
        # Log pruning cycle (passive only)
        tokens_freed = sum(len(v) for v in vectors_pruned)
        self.telemetry.log_pruning_cycle(
            vectors_pruned=len(vectors_pruned),
            tokens_freed=tokens_freed,
            rpr_before=self.config.RPR_CURRENT,
            rpr_after=self.config.RPR_CURRENT,  # Updated by pruning logic
        )
        
        # Update state
        self.last_pruning_cycle = now
        self.consecutive_safe_cycles = max(0, self.consecutive_safe_cycles - 1)
        
        # Add to telemetry buffer
        summary = self.telemetry.get_telemetry_summary()
        self.telemetry_buffer.append({
            "timestamp": now.isoformat(),
            "summary": summary,
            "pruned": len(vectors_pruned),
            "retained": len(vectors_to_prune) - len(vectors_pruned),
        })
        
        # Trim buffer
        if len(self.telemetry_buffer) > self.telemetry_buffer_size:
            self.telemetry_buffer = self.telemetry_buffer[-self.telemetry_buffer_size:]
        
        return summary
    
    def get_scheduler_status(self) -> dict:
        """
        Get scheduler status summary.
        """
        
        return {
            "last_pruning_cycle": self.last_pruning_cycle,
            "consecutive_safe_cycles": self.consecutive_safe_cycles,
            "telemetry_buffer_size": len(self.telemetry_buffer),
            "active_hours": self.SCHEDULER_ACTIVE_HOURS,
            "interval_minutes": self.PRUNING_CYCLE_INTERVAL_MINUTES,
            "window_size": self.WINDOW_SIZE,
            "priority_order": [(k, "DESC" if v else "ASC") for k, v in self.PRUNING_KEY_ORDER],
        }
    
    def get_telemetry_summary(self) -> dict:
        """
        Get aggregated telemetry summary.
        """
        
        return self.telemetry.get_telemetry_summary()
    
    def reset_scheduler(self) -> None:
        """
        Reset scheduler state (passive only).
        """
        
        self.last_pruning_cycle = None
        self.consecutive_safe_cycles = 0
        self.telemetry_buffer = []


# ------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------
if __name__ == '__main__':
    print("🚀 Phase 6.2 Deterministic Scheduling Configuration Loaded")
    print("   H1 Constraint: Passive telemetry only")
    print("   Schedule: Every 60 minutes (06:00-23:00)")
    print("   Pruning Order: last_access_time DESC → TRI score DESC → relevance DESC")
    print(f"   Window Size: {DeterministicScheduler.WINDOW_SIZE} task outputs")
    print("✅ Configuration ready for deterministic pruning cycles.")
