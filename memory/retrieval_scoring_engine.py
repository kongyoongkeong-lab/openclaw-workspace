#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieval Intelligence Layer - Phase P2.1
Retrieval Scoring Engine with Adaptive Weighting
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import math


class RetrievalScoringEngine:
    """
    Unified retrieval scoring model with adaptive weighting.
    
    Formula:
    retrieval_score = (
        task_affinity * 0.30 +
        governance_relevance * 0.25 +
        unresolved_dependency * 0.20 +
        recency_decay * 0.10 +
        semantic_uniqueness * 0.10 -
        compression_cost * 0.05
    )
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = {
            "weights": {
                "task_affinity": 0.30,
                "governance_relevance": 0.25,
                "unresolved_dependency": 0.20,
                "recency_decay": 0.10,
                "semantic_uniqueness": 0.10,
                "compression_cost": 0.05
            },
            "recency_decay": {
                "half_life_hours": 24,
                "min_weight": 0.01
            },
            "semantic_uniqueness": {
                "threshold": 0.30,  # Below this, penalty applies
                "penalty_multiplier": 0.5
            }
        }
        self.recent_injections = set()  # Track recently injected memory ids
        self.injection_counts = {}  # Track injection frequency per source
        self.semantic_cache = {}  # Track semantic content hashes
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load scoring configuration from file."""
        try:
            with open(config_path, 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            pass  # Use defaults
    
    def calculate_recency_decay(self, timestamp: float) -> float:
        """
        Calculate recency weight based on half-life decay.
        
        Formula: weight = min(0.1, 0.1 * e^(-ln(2) * delta / half_life_hours))
        """
        now = time.time()
        delta_hours = (now - timestamp) / 3600
        
        decay_factor = math.exp(-math.log(2) * delta_hours / self.config["recency_decay"]["half_life_hours"])
        raw_weight = 0.1 * decay_factor
        return max(raw_weight, self.config["recency_decay"]["min_weight"])
    
    def calculate_semantic_uniqueness(self, content: str) -> float:
        """
        Calculate semantic uniqueness score.
        
        Returns uniqueness score between 0.0 (completely repetitive) and 1.0 (unique).
        """
        content_hash = hash(content) % (2**32)
        uniqueness = 0.7 + (content_hash % 300) / 1000
        
        # Check against recently injected content
        if content in self.recent_injections:
            uniqueness *= 0.5  # Penalty for recent repetition
        
        return max(0.0, min(1.0, uniqueness))
    
    def calculate_compression_cost(self, content_length: int, current_context_size: int) -> float:
        """
        Calculate compression cost penalty.
        
        Higher cost for items that consume more context relative to their utility.
        """
        ratio = content_length / max(current_context_size, 1)
        return min(ratio * 100, 1.0)  # Cap at 100% penalty
    
    def score_memory(self, memory_id: str, content: str, timestamp: float,
                    task_context: Optional[Dict] = None,
                    governance_context: Optional[Dict] = None,
                    dependency_info: Optional[Dict] = None,
                    current_context_size: int = 0) -> Tuple[float, Dict]:
        """
        Calculate composite retrieval score for a memory item.
        
        Returns: (score, breakdown)
        """
        # Task affinity: how relevant to current task
        task_affinity = self._calculate_task_affinity(task_context, memory_id)
        
        # Governance relevance: importance to active governance state
        governance_relevance = self._calculate_governance_relevance(governance_context, memory_id)
        
        # Unresolved dependency: critical for dependencies
        unresolved_dependency = self._calculate_dependency_score(dependency_info)
        
        # Recency decay: freshness weight
        recency_weight = self.calculate_recency_decay(timestamp)
        
        # Semantic uniqueness: avoid repetition
        semantic_uniqueness = self.calculate_semantic_uniqueness(content)
        
        # Compression cost: context consumption penalty
        compression_cost = self.calculate_compression_cost(len(content), current_context_size)
        
        # Composite score
        score = (
            task_affinity * self.config["weights"]["task_affinity"] +
            governance_relevance * self.config["weights"]["governance_relevance"] +
            unresolved_dependency * self.config["weights"]["unresolved_dependency"] +
            recency_weight * self.config["weights"]["recency_decay"] +
            semantic_uniqueness * self.config["weights"]["semantic_uniqueness"] -
            compression_cost * self.config["weights"]["compression_cost"]
        )
        
        # Track injection
        self.recent_injections.add(memory_id)
        self.recent_injections.discard(self._normalize_id(memory_id, 72))  # 72h window
        
        self.injection_counts[memory_id] = self.injection_counts.get(memory_id, 0) + 1
        
        breakdown = {
            "task_affinity": task_affinity,
            "governance_relevance": governance_relevance,
            "unresolved_dependency": unresolved_dependency,
            "recency": recency_weight,
            "uniqueness": semantic_uniqueness,
            "compression_cost": compression_cost,
            "raw_score": score
        }
        
        return score, breakdown
    
    def _calculate_task_affinity(self, task_context: Optional[Dict], memory_id: str) -> float:
        """
        Calculate task affinity score.
        
        Higher affinity for memories that match current task keywords/tags.
        """
        if not task_context:
            return 0.3
        
        task_keywords = task_context.get("keywords", [])
        task_tags = task_context.get("tags", [])
        
        # Check if memory id matches task tags
        if memory_id in task_tags or any(tag in memory_id for tag in task_tags):
            return 0.9
        elif task_keywords:
            # Simple keyword matching (would be enhanced with embeddings in production)
            memory_lower = memory_id.lower()
            matches = sum(1 for kw in task_keywords if kw.lower() in memory_lower)
            return 0.5 + (matches * 0.1)
        else:
            return 0.3
    
    def _calculate_governance_relevance(self, governance_context: Optional[Dict], memory_id: str) -> float:
        """
        Calculate governance relevance score.
        
        Higher relevance for memories addressing active anomalies or critical thresholds.
        """
        if not governance_context:
            return 0.2
        
        active_anomalies = governance_context.get("active_anomalies", [])
        critical_thresholds = governance_context.get("critical_thresholds", [])
        
        # Check if memory references active anomaly
        for anomaly in active_anomalies:
            if memory_id in str(anomaly) or any(t in memory_id for t in anomaly.get("tags", [])):
                return 0.8
        
        # Check critical thresholds
        for threshold in critical_thresholds:
            if memory_id in str(threshold) or any(t in memory_id for t in threshold.get("tags", [])):
                return 0.7
        
        return 0.2
    
    def _calculate_dependency_score(self, dependency_info: Optional[Dict]) -> float:
        """
        Calculate unresolved dependency score.
        
        Higher for memories that address dependency chains.
        """
        if not dependency_info:
            return 0.2
        
        unresolved_deps = dependency_info.get("unresolved", [])
        resolved_deps = dependency_info.get("resolved", [])
        
        # Check memory in unresolved deps
        if memory_id in unresolved_deps:
            return 0.85
        
        # Check memory resolves deps
        if memory_id in resolved_deps:
            return 0.6
        
        return 0.2
    
    def _normalize_id(self, memory_id: str, window_hours: int) -> str:
        """Normalize memory id for recent injection tracking."""
        base_id = memory_id.split(":")[0] if ":" in memory_id else memory_id
        return f"{base_id}:recent"
    
    def score_memory_batch(self, memories: List[Dict], current_context_size: int = 0,
                          task_context: Optional[Dict] = None) -> List[Tuple[str, float, Dict]]:
        """
        Score a batch of memories and return sorted results.
        
        Returns: List of (memory_id, score, breakdown) sorted by score descending
        """
        scored = []
        for mem in memories:
            score, breakdown = self.score_memory(
                memory_id=mem["id"],
                content=mem["content"],
                timestamp=mem.get("timestamp", time.time()),
                task_context=task_context,
                governance_context=mem.get("governance_context"),
                dependency_info=mem.get("dependency_info"),
                current_context_size=current_context_size
            )
            scored.append((mem["id"], score, breakdown))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored
    
    def calculate_pressure_zone(self, context_usage: float, gpu_usage: float) -> str:
        """
        Determine current pressure zone based on system metrics.
        
        Returns: pressure_zone string
        """
        context_critical = context_usage > 0.85
        gpu_critical = gpu_usage > 0.95
        
        if context_critical or gpu_critical:
            return "EMERGENCY"
        elif context_usage > 0.75 or gpu_usage > 0.90:
            return "CRITICAL"
        elif context_usage > 0.65 or gpu_usage > 0.85:
            return "PREEMPTIVE"
        elif context_usage > 0.55 or gpu_usage > 0.75:
            return "EARLY_CONTROL"
        else:
            return "SAFE"
    
    def get_adaptive_top_k(self, pressure_zone: str) -> int:
        """
        Get adaptive top_k based on pressure zone.
        
        Policy:
        | Pressure Zone | top_k |
        | ------------- | ------ |
        | SAFE | 5 |
        | EARLY_CONTROL | 3 |
        | PREEMPTIVE | 2 |
        | CRITICAL | 1 |
        | EMERGENCY | 0 (freeze) |
        """
        policy = {
            "SAFE": 5,
            "EARLY_CONTROL": 3,
            "PREEMPTIVE": 2,
            "CRITICAL": 1,
            "EMERGENCY": 0
        }
        return policy.get(pressure_zone, 3)


# Configuration persistence
def save_scored_results(scored_memories: List[Tuple[str, float, Dict]], output_path: str):
    """Save scored results to JSONL."""
    with open(output_path, 'w') as f:
        for mem_id, score, breakdown in scored_memories:
            record = {
                "memory_id": mem_id,
                "score": round(score, 4),
                "breakdown": breakdown
            }
            f.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    # Demo scoring
    engine = RetrievalScoringEngine()
    
    # Test scoring
    task_ctx = {"keywords": ["context", "efficiency", "adaptive"]}
    mem = {
        "id": "task_affinity_test",
        "content": "This is a test memory for task affinity scoring.",
        "timestamp": time.time() - 3600,
        "governance_context": None,
        "dependency_info": None
    }
    
    score, breakdown = engine.score_memory(**mem, task_context=task_ctx)
    print(f"Memory Score: {score:.4f}")
    print(f"Breakdown: {breakdown}")
    
    # Pressure zone demo
    pressure_zone = engine.calculate_pressure_zone(0.72, 0.78)
    top_k = engine.get_adaptive_top_k(pressure_zone)
    print(f"\nPressure Zone: {pressure_zone}")
    print(f"Adaptive top_k: {top_k}")
