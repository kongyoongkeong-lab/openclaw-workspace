#!/usr/bin/env python3
"""
Phase 6.1 — RPR Stabilization Configuration
Context Pruning Thresholds for OpenClaw (H1-Compliant)

Target RPR: ≤0.06 (down from 0.09)
Strategy: Aggressive unused token + TRI-based pruning with sliding window retention.

⚠️ H1 Constraint: Passive telemetry only. No governance actions triggered.
"""

import os
from typing import Optional
from datetime import datetime, timedelta
import hashlib

# ----------------------------------------------------------------------
# H1 METRICS LATCH (Read-Only — No Modifications Permitted)
# ----------------------------------------------------------------------
H1_METRICS = {
    "GAF_TARGET": 0.10,
    "GAF_CURRENT": 0.25,
    "RPR_TARGET": 0.06,  # Phase 6.1 target
    "RPR_CURRENT": 0.09,  # Current (critical watch)
    "DETERMINISM_TARGET": 1.0,
    "DETERMINISM_CURRENT": 1.0,  # Locked
    "VRAM_LIMIT": 9.5,  # GB
    "GPU_TARGET": 0.85,  # 85% sustained
}

# ----------------------------------------------------------------------
# CONTEXT PRUNING CONFIGURATION
# ----------------------------------------------------------------------
class ContextPruningConfig:
    """
    H1-Compliant context pruning rules for RPR stabilization.
    
    All pruning actions are passive telemetry only.
    No governance actions triggered automatically.
    """
    
    # 1. UNUSED TOKEN PRUNING
    UNUSED_TOKEN_THRESHOLD_TURNS: int = 8
    UNUSED_TOKEN_PRUNING_WEIGHT: float = 0.7
    
    # 2. TRI VECTOR PRUNING
    TRI_LOW_THRESHOLD: float = 0.5
    TRI_PRUNING_WEIGHT: float = 0.3
    
    # 3. SLIDING WINDOW
    SLIDING_WINDOW_SIZE: int = 50  # Task outputs retained
    
    # 4. TOOL OUTPUT CACHING
    HIGH_VALUE_TOOLS = [
        'web_search',
        'tavily_search',
        'memory_search',
        'pdf_parse',
        'image',
        'pdf',
    ]
    
    CACHE_TTL_TURNS: int = 3  # Reuse for 3 consecutive tasks
    
    # 5. RETRIEVAL BUDGET
    MAX_TOKENS_PER_TASK: int = 1200
    MAX_VECTOR_QUERIES_PER_TASK: int = 3
    
    # 6. PRUNING ORDER (Deterministic)
    PRUNING_KEY_ORDER: list[str] = [
        'last_access_time',  # DESC
        'tri_score',         # DESC
        'relevance',         # DESC
    ]

# ----------------------------------------------------------------------
# DETERMINISTIC UTILITY FUNCTIONS
# ----------------------------------------------------------------------
class DeterministicPruner:
    """
    H1-compliant deterministic pruning utilities.
    
    Pruning order: last_access_time DESC → TRI score DESC → relevance DESC
    High-value vectors always prioritized for retention.
    """
    
    def __init__(self, config: ContextPruningConfig):
        self.config = config
    
    def compute_pruning_priority(
        self,
        vector: dict,
        now: datetime,
    ) -> tuple[float, str]:
        """
        Compute deterministic priority for pruning.
        
        Returns: (priority_score, sort_key)
        Higher priority_score = lower pruning risk.
        """
        
        last_access = vector.get('last_access_time', now)
        time_diff = (now - last_access).total_seconds() / 3600  # hours
        
        # Time decay (heavier penalty for old vectors)
        time_penalty = min(time_diff / 24, 1.0)  # Cap at 1.0 (24h)
        
        # TRI score (lower TRI = higher pruning risk)
        tri_penalty = 1.0 - vector.get('tri_score', 0.5)
        
        # Relevance (lower relevance = higher pruning risk)
        relevance_penalty = 1.0 - vector.get('relevance', 0.5)
        
        # Combined penalty (deterministic)
        penalty = (
            self.config.UNUSED_TOKEN_PRUNING_WEIGHT * time_penalty +
            self.config.TRI_PRUNING_WEIGHT * tri_penalty +
            (1.0 - self.config.UNUSED_TOKEN_PRUNING_WEIGHT - self.config.TRI_PRUNING_WEIGHT) * relevance_penalty
        )
        
        # Sort key: negative penalty (so lower penalty = higher priority)
        sort_key = f"{now}_{self.config.TRI_LOW_THRESHOLD}_{self.config.HIGH_VALUE_TOOLS}"
        
        return -penalty, sort_key
    
    def should_prune_vector(
        self,
        vector: dict,
        now: datetime,
    ) -> bool:
        """
        Determine if a vector should be pruned.
        
        Returns True if vector should be pruned.
        Always False for HIGH_VALUE_TOOLS outputs.
        """
        
        # Never prune high-value tool outputs
        if vector.get('source_tool') in self.config.HIGH_VALUE_TOOLS:
            return False
        
        # Check unused token threshold
        last_access = vector.get('last_access_time', now)
        time_diff = (now - last_access).total_seconds() / 3600  # hours
        
        if time_diff > 24 * self.config.UNUSED_TOKEN_THRESHOLD_TURNS:
            return True
        
        # Check TRI threshold
        tri_score = vector.get('tri_score', 0.5)
        if tri_score < self.config.TRI_LOW_THRESHOLD:
            return True
        
        return False

# ----------------------------------------------------------------------
# PASSIVE TELEMETRY HOOKS
# ----------------------------------------------------------------------
class PassiveTelemetryHook:
    """
    Passive telemetry hooks for RPR stabilization.
    
    Tracks:
    - RPR after each pruning cycle
    - Tokens freed
    - Vectors pruned
    
    No governance actions triggered — purely observational.
    """
    
    def __init__(self, config: ContextPruningConfig):
        self.config = config
        self.telemetry_log = []
    
    def log_pruning_cycle(
        self,
        vectors_pruned: int,
        tokens_freed: int,
        rpr_before: float,
        rpr_after: float,
    ) -> None:
        """
        Log pruning cycle telemetry (passive only).
        """
        
        entry = {
            'timestamp': datetime.now(),
            'vectors_pruned': vectors_pruned,
            'tokens_freed': tokens_freed,
            'rpr_before': rpr_before,
            'rpr_after': rpr_after,
            'delta_rpr': rpr_after - rpr_before,
        }
        
        self.telemetry_log.append(entry)
        print(f"📊 Telemetry: {vectors_pruned} vectors pruned, {tokens_freed} tokens freed, RPR {rpr_before:.2f}→{rpr_after:.2f}")
    
    def get_telemetry_summary(self) -> dict:
        """
        Get telemetry summary for this pruning cycle.
        """
        
        if not self.telemetry_log:
            return {
                'total_cycles': 0,
                'total_vectors_pruned': 0,
                'total_tokens_freed': 0,
                'avg_rpr_reduction': 0.0,
            }
        
        total_vectors = sum(e['vectors_pruned'] for e in self.telemetry_log)
        total_tokens = sum(e['tokens_freed'] for e in self.telemetry_log)
        rpr_improvements = [e['delta_rpr'] for e in self.telemetry_log]
        
        return {
            'total_cycles': len(self.telemetry_log),
            'total_vectors_pruned': total_vectors,
            'total_tokens_freed': total_tokens,
            'avg_rpr_reduction': sum(rpr_improvements) / len(rpr_improvements) if rpr_improvements else 0.0,
        }

# ----------------------------------------------------------------------
# MAIN ENTRY POINT
# ----------------------------------------------------------------------
if __name__ == '__main__':
    print("🚀 Phase 6.1 RPR Stabilization Configuration Loaded")
    print("   H1 Constraint: Passive telemetry only")
    print("   Target RPR: ≤0.06")
    
    config = ContextPruningConfig()
    pruner = DeterministicPruner(config)
    telemetry = PassiveTelemetryHook(config)
    
    print(f"   Unused Token Threshold: {config.UNUSED_TOKEN_THRESHOLD_TURNS} turns")
    print(f"   Low TRI Threshold: {config.TRI_LOW_THRESHOLD}")
    print(f"   Sliding Window Size: {config.SLIDING_WINDOW_SIZE}")
    print(f"   High-Value Tools Preserved: {config.HIGH_VALUE_TOOLS}")
    print(f"   Max Tokens/Task: {config.MAX_TOKENS_PER_TASK}")
    print(f"   Max Vector Queries/Task: {config.MAX_VECTOR_QUERIES_PER_TASK}")
    print("✅ Configuration ready for passive telemetry.")
