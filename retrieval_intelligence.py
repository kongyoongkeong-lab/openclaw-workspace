#!/usr/bin/env python3
"""
retrieval_intelligence.py - Retrieval Intelligence Layer (P2)

Implements:
- P2.1: Unified Retrieval Scoring Engine
- P2.2: Adaptive top_k based on pressure zone
- P2.3: Retrieval Budget Leasing
- P2.4: Retrieval Cooldown Memory
- P2.5: Retrieval Effectiveness Telemetry

Formula:
retrieval_score = (
    task_affinity * 0.30 +
    governance_relevance * 0.25 +
    unresolved_dependency * 0.20 +
    recency_decay * 0.10 +
    semantic_uniqueness * 0.10 -
    compression_cost * 0.05
)

Pressure Zone top_k Policy:
| Zone          | top_k |
| ------------- | ----- |
| SAFE          | 5     |
| EARLY_CONTROL | 3     |
| PREEMPTIVE    | 2     |
| CRITICAL      | 1     |
| EMERGENCY     | 0     |
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
import math
from datetime import datetime, timedelta
from memory_v1 import init_memory_system
from spg import get_sp_governor

# ============================================================================
# P2.1: RETRIEVAL SCORING ENGINE
# ============================================================================
@dataclass
class MemoryItemScore:
    """
    Unified scoring model for memory retrieval.
    
    Weighted formula:
    retrieval_score = (
        task_affinity * 0.30 +
        governance_relevance * 0.25 +
        unresolved_dependency * 0.20 +
        recency_decay * 0.10 +
        semantic_uniqueness * 0.10 -
        compression_cost * 0.05
    )
    """
    task_affinity: float = 0.0       # How relevant to current task (0-1)
    governance_relevance: float = 0.0  # Alignment with governance rules (0-1)
    unresolved_dependency: float = 0.0  # Critical unresolved issues (0-1)
    recency_decay: float = 0.0       # Freshness factor (0-1, higher = more recent)
    semantic_uniqueness: float = 0.0  # Diversity suppression (0-1, higher = more unique)
    compression_cost: float = 0.0    # How expensive to compress (0-1)
    
    # Calculated score
    score: float = field(init=False)
    
    # Metadata
    content_hash: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self):
        """Calculate weighted retrieval score."""
        self.score = (
            self.task_affinity * 0.30 +
            self.governance_relevance * 0.25 +
            self.unresolved_dependency * 0.20 +
            self.recency_decay * 0.10 +
            self.semantic_uniqueness * 0.10 -
            self.compression_cost * 0.05
        )
        self.content_hash = hashlib.sha256(
            f"{self.task_affinity}{self.governance_relevance}{self.unresolved_dependency}"
            f"{self.recency_decay}{self.semantic_uniqueness}".encode()
        ).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryItemScore':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================================
# P2.4: RETRIEVAL COOLDOWN MEMORY
# ============================================================================
@dataclass
class RetrievalCooldownEntry:
    """Track recently injected memories to prevent recursion loops."""
    content_hash: str
    inject_timestamp: float
    cooldown_ms: int = 5000  # Default 5 second cooldown
    penalty_multiplier: float = 1.0  # Repetition penalty multiplier
    
    def is_expired(self) -> bool:
        """Check if cooldown has expired."""
        return (time.time() * 1000) - self.inject_timestamp >= self.cooldown_ms
    
    def get_remaining_cooldown(self) -> int:
        """Get remaining cooldown in milliseconds."""
        now_ms = int(time.time() * 1000)
        if now_ms < self.inject_timestamp + self.cooldown_ms:
            return self.inject_timestamp + self.cooldown_ms - now_ms
        return 0


class RetrievalCooldownManager:
    """
    Prevent retrieval recursion loops.
    
    Tracks:
    - Recently injected memories
    - Retrieval frequency
    - Compression repetition
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.cooldown_db: Dict[str, RetrievalCooldownEntry] = {}
        self.cooldown_file = workspace / "retrieval_cooldowns.jsonl"
        self._load_cooldowns()
    
    def _load_cooldowns(self):
        """Load cooldown entries from persistent storage."""
        if not self.cooldown_file.exists():
            return
        with open(self.cooldown_file) as f:
            for line in f:
                data = json.loads(line.strip())
                self.cooldown_db[data["content_hash"]] = RetrievalCooldownEntry(
                    content_hash=data["content_hash"],
                    inject_timestamp=data["inject_timestamp"],
                    cooldown_ms=data.get("cooldown_ms", 5000),
                    penalty_multiplier=data.get("penalty_multiplier", 1.0)
                )
    
    def _save_cooldowns(self):
        """Persist cooldown entries."""
        with open(self.cooldown_file, "w") as f:
            for entry in self.cooldown_db.values():
                f.write(json.dumps({
                    "content_hash": entry.content_hash,
                    "inject_timestamp": entry.inject_timestamp,
                    "cooldown_ms": entry.cooldown_ms,
                    "penalty_multiplier": entry.penalty_multiplier
                }) + "\n")
    
    def record_injection(self, content_hash: str, penalty_multiplier: float = 1.0):
        """Record a memory injection and apply cooldown."""
        now_ms = time.time() * 1000
        
        # Remove expired entries
        expired_hashes = [
            h for h, e in self.cooldown_db.items() 
            if e.is_expired()
        ]
        for h in expired_hashes:
            del self.cooldown_db[h]
        
        # Check if this hash is already in cooldown
        if content_hash in self.cooldown_db:
            existing = self.cooldown_db[content_hash]
            # Extend cooldown if not expired
            if not existing.is_expired():
                existing.cooldown_ms += 5000  # Add 5 seconds
                existing.penalty_multiplier = max(
                    existing.penalty_multiplier + 0.5, 
                    1.0
                )  # Increase penalty for repetition
            else:
                # Clear old entry, create new one
                del self.cooldown_db[content_hash]
        
        self.cooldown_db[content_hash] = RetrievalCooldownEntry(
            content_hash=content_hash,
            inject_timestamp=now_ms,
            cooldown_ms=5000,
            penalty_multiplier=penalty_multiplier
        )
        
        # Only save if we have significant entries
        if len(self.cooldown_db) > 100:
            self._save_cooldowns()
    
    def get_penalty_multiplier(self, content_hash: str) -> float:
        """Get current penalty multiplier for a content hash."""
        if content_hash in self.cooldown_db:
            entry = self.cooldown_db[content_hash]
            if entry.is_expired():
                del self.cooldown_db[content_hash]
                return 1.0
            return entry.penalty_multiplier
        return 1.0
    
    def get_remaining_cooldown(self, content_hash: str) -> int:
        """Get remaining cooldown for a content hash."""
        if content_hash in self.cooldown_db:
            entry = self.cooldown_db[content_hash]
            if entry.is_expired():
                del self.cooldown_db[content_hash]
                return 0
            return entry.get_remaining_cooldown()
        return 0
    
    def should_allow_retrieval(self, content_hash: str) -> Tuple[bool, int, float]:
        """
        Check if retrieval should be allowed for this content.
        Returns: (allowed, remaining_ms, penalty_multiplier)
        """
        remaining_ms = self.get_remaining_cooldown(content_hash)
        penalty = self.get_penalty_multiplier(content_hash)
        
        return (remaining_ms == 0, remaining_ms, penalty)
    
    def prune_expired(self):
        """Remove all expired cooldown entries."""
        expired_hashes = [
            h for h, e in self.cooldown_db.items() 
            if e.is_expired()
        ]
        for h in expired_hashes:
            del self.cooldown_db[h]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cooldown manager statistics."""
        active = sum(1 for e in self.cooldown_db.values() if not e.is_expired())
        total_injections = len(self.cooldown_db)
        return {
            "active_cooldowns": active,
            "total_injections_tracked": total_injections,
            "expired": total_injections - active,
        }
    
    def __del__(self):
        """Clean up on deletion."""
        self._save_cooldowns()


# ============================================================================
# P2.2: ADAPTIVE top_k
# ============================================================================
ADAPTIVE_TOP_K_POLICY = {
    "SAFE": 5,
    "EARLY_CONTROL": 3,
    "PREEMPTIVE": 2,
    "CRITICAL": 1,
    "EMERGENCY": 0,  # Freeze retrieval
}


class AdaptiveTopKManager:
    """
    Dynamic top_k based on pressure zone.
    
    Aligns retrieval directly with SPG/PCG state.
    """
    
    def __init__(self):
        self.zone_to_topk = ADAPTIVE_TOP_K_POLICY
    
    def get_top_k(self, zone: str) -> int:
        """Get top_k for current pressure zone."""
        return self.zone_to_topk.get(zone.upper(), 5)
    
    def should_freeze_retrieval(self, zone: str) -> bool:
        """Check if retrieval should be frozen (EMERGENCY zone)."""
        return zone.upper() == "EMERGENCY"


# ============================================================================
# P2.3: RETRIEVAL BUDGET LEASING
# ============================================================================
@dataclass
class RetrievalBudgetPool:
    """
    Shared retrieval budget pool for multi-agent scaling.
    
    Example:
    - global retrieval budget = 12
    - @intel consumes 5
    - @ops consumes 3
    - @comms consumes 1
    - reserve buffer = 3
    """
    global_budget: int = 12
    consumed: int = 0
    by_agent: Dict[str, int] = field(default_factory=dict)
    reserve_buffer: int = 3
    
    def add(self, agent: str, amount: int) -> bool:
        """
        Add to agent's consumption.
        Returns True if within budget, False if over.
        """
        available = self.global_budget - self.consumed
        agent_amount = self.by_agent.get(agent, 0)
        
        if agent_amount + amount <= available + self.reserve_buffer:
            self.consumed += amount
            self.by_agent[agent] = agent_amount + amount
            return True
        return False
    
    def subtract(self, agent: str, amount: int) -> bool:
        """Subtract from agent's consumption."""
        agent_amount = self.by_agent.get(agent, 0)
        
        if agent_amount >= amount:
            self.consumed -= amount
            self.by_agent[agent] = agent_amount - amount
            return True
        return False
    
    def get_available(self, agent: str = None) -> int:
        """Get available budget for an agent (or globally)."""
        return self.global_budget - self.consumed
    
    def get_agent_balance(self, agent: str) -> int:
        """Get current balance for an agent."""
        return self.by_agent.get(agent, 0)
    
    def get_remaining_buffer(self) -> int:
        """Get remaining reserve buffer."""
        return max(0, self.global_budget - self.consumed - sum(self.by_agent.values()))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "global_budget": self.global_budget,
            "consumed": self.consumed,
            "available": self.global_budget - self.consumed,
            "reserve_buffer": self.reserve_buffer,
            "by_agent": self.by_agent,
        }


# ============================================================================
# P2.5: RETRIEVAL EFFECTIVENESS TELEMETRY
# ============================================================================
@dataclass
class RetrievalMetric:
    """Track retrieval effectiveness metrics."""
    timestamp: float = field(default_factory=time.time)
    retrieval_usefulness_ratio: float = 0.0  # How many retrieved items were used
    injected_memory_used_count: int = 0      # Count of actually used memories
    retrieval_discard_rate: float = 0.0      # Rate of discarded retrievals
    retrieval_to_output_ratio: float = 0.0   # Contribution ratio
    effective_context_density: float = 0.0   # Useful reasoning tokens / total context
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RetrievalTelemetryManager:
    """
    Mandatory telemetry for retrieval effectiveness.
    
    Tracks:
    - retrieval_usefulness_ratio
    - injected_memory_used %
    - retrieval_discard_rate
    - retrieval_to_output_contribution_ratio
    - effective_context_density (key KPI)
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.telemetry_dir = workspace / "telemetry"
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.current_metrics: Dict[str, Any] = {
            "retrieval_usefulness_ratio": 0.0,
            "injected_memory_used_count": 0,
            "total_retrievals": 0,
            "discarded_retrievals": 0,
            "total_retrieved": 0,
            "useful_reasoning_tokens": 0,
            "total_context_tokens": 0,
        }
        self.history_file = self.telemetry_dir / "retrieval_history.jsonl"
    
    def record_retrieval(self, retrieved: int, useful: int = None):
        """
        Record a retrieval event.
        
        Args:
            retrieved: Number of items retrieved
            useful: Number of items actually used (if None, assume all useful)
        """
        self.current_metrics["total_retrievals"] += retrieved
        self.current_metrics["total_retrieved"] += retrieved
        
        if useful is None:
            useful = retrieved
        elif useful < 0:
            useful = 0
        
        self.current_metrics["useful_reasoning_tokens"] += useful
        self.current_metrics["total_context_tokens"] += retrieved * 512  # Approx tokens per item
    
    def record_usage(self, used_count: int):
        """Record memory usage events."""
        self.current_metrics["injected_memory_used_count"] += used_count
    
    def record_discard(self, count: int):
        """Record discarded retrievals."""
        self.current_metrics["discarded_retrievals"] += count
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics with calculated ratios."""
        m = self.current_metrics.copy()
        
        # Calculate ratios
        if m["total_retrieved"] > 0:
            m["retrieval_usefulness_ratio"] = m["useful_reasoning_tokens"] / m["total_context_tokens"]
            m["retrieval_discard_rate"] = m["discarded_retrievals"] / m["total_retrievals"] if m["total_retrievals"] > 0 else 0
        
        if m["total_context_tokens"] > 0:
            m["effective_context_density"] = m["useful_reasoning_tokens"] / m["total_context_tokens"]
        
        # Injected memory used percentage
        if m["total_retrieved"] > 0:
            m["injected_memory_used_pct"] = (m["injected_memory_used_count"] / m["total_retrieved"]) * 100
        
        return {
            "timestamp": datetime.fromtimestamp(m["timestamp"]).isoformat(),
            "retrieval_usefulness_ratio": round(m["retrieval_usefulness_ratio"], 4),
            "injected_memory_used_pct": round(m["injected_memory_used_pct"], 2),
            "retrieval_discard_rate": round(m["retrieval_discard_rate"], 4),
            "retrieval_to_output_ratio": round(m["retrieval_usefulness_ratio"], 4),
            "effective_context_density": round(m["effective_context_density"], 4),
            "total_retrievals": m["total_retrievals"],
            "useful_reasoning_tokens": m["useful_reasoning_tokens"],
        }
    
    def save_metrics(self):
        """Save metrics to history file."""
        with open(self.history_file, "a") as f:
            f.write(json.dumps(self.get_metrics()) + "\n")
    
    def reset(self):
        """Reset metrics (call after task completion)."""
        self.current_metrics = {
            "retrieval_usefulness_ratio": 0.0,
            "injected_memory_used_count": 0,
            "total_retrievals": 0,
            "discarded_retrievals": 0,
            "total_retrieved": 0,
            "useful_reasoning_tokens": 0,
            "total_context_tokens": 0,
        }


# ============================================================================
# P2: RETRIEVAL INTELLIGENCE LAYER - MAIN CLASS
# ============================================================================
class RetrievalIntelligenceLayer:
    """
    Complete P2 Retrieval Intelligence Layer.
    
    Integrates:
    - P2.1: Retrieval Scoring Engine
    - P2.2: Adaptive top_k
    - P2.3: Retrieval Budget Leasing
    - P2.4: Retrieval Cooldown Memory
    - P2.5: Retrieval Effectiveness Telemetry
    """
    
    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.memory = init_memory_system(workspace)
        self.spg = get_sp_governor()
        
        # P2.1: Scoring Engine
        self.current_query: Optional[str] = None
        self.retrieval_pool: List[MemoryItemScore] = []
        
        # P2.4: Cooldown Manager
        self.cooldown_manager = RetrievalCooldownManager(workspace)
        
        # P2.2: Adaptive top_k
        self.topk_manager = AdaptiveTopKManager()
        
        # P2.3: Budget Pool
        self.budget_pool = RetrievalBudgetPool()
        
        # P2.5: Telemetry
        self.telemetry = RetrievalTelemetryManager(workspace)
        
        # Initialize budget allocation
        self.budget_pool.add("intel", 5)
        self.budget_pool.add("ops", 3)
        self.budget_pool.add("comms", 1)
        self.budget_pool.add("reserve", 3)  # Already in global_budget, so this is just tracking
    
    def _calculate_pressure_zone(self) -> str:
        """Get current pressure zone from SPG."""
        pressure_data = self.spg.calculate_pressure()
        return pressure_data["zone"]
    
    def _calculate_recency_decay(self, timestamp: float) -> float:
        """Calculate recency decay based on how old the memory is."""
        now = time.time()
        age = now - timestamp
        # Decay to 0 after 7 days
        decay_factor = max(0, 1 - (age / (7 * 24 * 3600)))
        return decay_factor
    
    def retrieve_memories(self, query: str) -> List[Dict[str, Any]]:
        """
        Main retrieval interface with P2 intelligence.
        
        Args:
            query: Search query string
        
        Returns:
            List of memory items with scores
        """
        # Record this retrieval
        self.telemetry.record_retrieval(1)
        
        # Get pressure zone
        zone = self._calculate_pressure_zone()
        
        # Apply retrieval cooldown penalty
        if zone in ["CRITICAL", "EMERGENCY"]:
            return []  # No retrieval in critical zones
        
        # Initialize query tracking
        self.current_query = query
        
        # Build task affinity based on query
        task_affinity = 0.8 if query else 0.5
        
        # Get current budget available
        available_budget = self.budget_pool.get_available()
        
        # Limit retrievals based on budget
        max_retrievals = min(available_budget, self.topk_manager.get_top_k(zone))
        
        # Retrieve and score memories
        scored_items = []
        
        # Note: In production, this would query vector DB
        # For now, we demonstrate the scoring mechanism
        
        # Get recent episodic memories
        episodic_memories = self.memory.get_episodic_memories(limit=max_retrievals * 2)
        
        for i, mem in enumerate(episodic_memories):
            if self.budget_pool.get_available() <= 0:
                break
            
            # Calculate scores for each dimension
            task_affinity = task_affinity * (1 - i * 0.05)  # Diminishing returns
            governance_relevance = 0.7 + (i % 3) * 0.1  # Example calculation
            unresolved_dependency = 0.3 if "critical" in mem.get("context", "").lower() else 0.0
            recency_decay = self._calculate_recency_decay(mem.get("timestamp", time.time()))
            
            # Semantic uniqueness check
            is_unique = not any(
                item.semantic_uniqueness > 0.8 
                for item in self.retrieval_pool 
                if item.content_hash == mem.get("content_hash", "")
            )
            semantic_uniqueness = 0.9 if is_unique else 0.3
            
            # Compression cost (simplified)
            compression_cost = 0.1 if mem.get("compressed", False) else 0.0
            
            # Get penalty multiplier from cooldown manager
            penalty_multiplier = self.cooldown_manager.get_penalty_multiplier(mem.get("content_hash", ""))
            
            # Create scored item
            scored_item = MemoryItemScore(
                task_affinity=task_affinity,
                governance_relevance=governance_relevance,
                unresolved_dependency=unresolved_dependency,
                recency_decay=recency_decay,
                semantic_uniqueness=semantic_uniqueness,
                compression_cost=compression_cost,
                penalty_multiplier=penalty_multiplier
            )
            
            # Apply penalty multiplier to final score
            scored_item.score *= penalty_multiplier
            
            # Check cooldown
            allowed, remaining_ms, _ = self.cooldown_manager.should_allow_retrieval(
                scored_item.content_hash
            )
            
            if not allowed:
                # Too recently retrieved - reduce score
                scored_item.score *= 0.3
            
            # Apply pressure zone penalty
            zone_penalty = {
                "SAFE": 1.0,
                "EARLY_CONTROL": 0.8,
                "PREEMPTIVE": 0.6,
                "CRITICAL": 0.4,
                "EMERGENCY": 0.0,
            }.get(zone, 1.0)
            
            scored_item.score *= zone_penalty
            
            scored_items.append(scored_item)
            
            # Consume budget
            if scored_item.score > 0:
                self.budget_pool.add("main", 1)
        
        # Sort by score descending
        scored_items.sort(key=lambda x: x.score, reverse=True)
        
        # Limit to adaptive top_k
        top_k = self.topk_manager.get_top_k(zone)
        self.retrieval_pool = scored_items[:top_k]
        
        # Record discarded items
        discarded = len(scored_items) - top_k
        if discarded > 0:
            self.telemetry.record_discard(discarded)
        
        # Prepare results
        results = []
        for item in self.retrieval_pool:
            results.append({
                "score": round(item.score, 4),
                "content_hash": item.content_hash,
                "penalty_multiplier": round(item.penalty_multiplier, 2),
                "task_affinity": round(item.task_affinity, 4),
                "governance_relevance": round(item.governance_relevance, 4),
                "unresolved_dependency": round(item.unresolved_dependency, 4),
                "recency_decay": round(item.recency_decay, 4),
                "semantic_uniqueness": round(item.semantic_uniqueness, 4),
                "compression_cost": round(item.compression_cost, 4),
            })
        
        # Save telemetry
        self.telemetry.save_metrics()
        
        return results
    
    def mark_as_used(self, item_hash: str):
        """Mark a retrieved item as actually used."""
        self.telemetry.record_usage(1)
    
    def get_effective_context_density(self) -> float:
        """Get the key KPI: effective context density."""
        metrics = self.telemetry.get_metrics()
        return metrics.get("effective_context_density", 0.0)
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get comprehensive health check."""
        pressure_data = self.spg.calculate_pressure()
        
        return {
            "pressure_zone": pressure_data["zone"],
            "pressure_index": pressure_data["pressure_index"],
            "budget": self.budget_pool.to_dict(),
            "cooldown_stats": self.cooldown_manager.get_stats(),
            "telemetry": self.telemetry.get_metrics(),
            "adaptive_top_k": self.topk_manager.get_top_k(pressure_data["zone"]),
            "retrieval_pool_size": len(self.retrieval_pool),
            "effective_context_density": self.get_effective_context_density(),
        }


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    workspace = Path("/home/jason2ykk/.openclaw/workspace")
    retrieval_layer = RetrievalIntelligenceLayer(workspace)
    
    print("🚀 Retrieval Intelligence Layer (P2) Initialized")
    print("=" * 50)
    print(f"Global Budget: {retrieval_layer.budget_pool.global_budget}")
    print(f"Current Zone: {retrieval_layer._calculate_pressure_zone()}")
    print(f"Adaptive top_k: {retrieval_layer.topk_manager.get_top_k(retrieval_layer._calculate_pressure_zone())}")
    print()
    
    print("Commands: retrieve, budget, cooldown, telemetry, health, quit\n")
    
    while True:
        try:
            cmd = input("Enter command: ")
            
            if cmd.strip().lower() in ["quit", "exit", "q"]:
                break
            
            elif cmd.strip().lower() == "health":
                print(json.dumps(retrieval_layer.get_health_check(), indent=2))
            
            elif cmd.strip().lower().startswith("retrieve "):
                query = cmd.strip().replace("retrieve ", "")
                results = retrieval_layer.retrieve_memories(query)
                
                if results:
                    print(f"📊 Retrieved {len(results)} items:")
                    for i, item in enumerate(results[:3], 1):
                        print(f"  {i}. Score: {item['score']:.4f}")
                        print(f"     Task Affinity: {item['task_affinity']:.2f}")
                        print(f"     Governance: {item['governance_relevance']:.2f}")
                        print(f"     Unresolved: {item['unresolved_dependency']:.2f}")
                        print(f"     Recency: {item['recency_decay']:.2f}")
                        print(f"     Uniqueness: {item['semantic_uniqueness']:.2f}")
                        print()
                else:
                    print("No retrievals (emergency zone or budget exhausted)")
            
            else:
                print("Unknown command")
                
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")
