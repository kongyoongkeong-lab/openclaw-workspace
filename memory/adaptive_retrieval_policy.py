#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retrieval Intelligence Layer - Phase P2.2
Adaptive top_k and Dynamic Retrieval Policy
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class PressureZone(Enum):
    """System pressure zones for adaptive retrieval policy."""
    SAFE = "safe"
    EARLY_CONTROL = "early_control"
    PREEMPTIVE = "preemptive"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class RetrievalPolicy:
    """
    Dynamic retrieval policy based on pressure zone.
    
    Maps pressure zone to:
    - top_k: number of results to retrieve
    - budget: retrieval budget allocation
    - cooldown: minimum seconds between retrievals
    - freeze: whether retrieval is frozen
    """
    
    SAFE: Dict = field(default_factory=lambda: {
        "top_k": 5,
        "budget": 12,
        "cooldown_seconds": 0.5,
        "freeze": False,
        "max_parallel": 3
    })
    
    EARLY_CONTROL: Dict = field(default_factory=lambda: {
        "top_k": 3,
        "budget": 10,
        "cooldown_seconds": 1.0,
        "freeze": False,
        "max_parallel": 2
    })
    
    PREEMPTIVE: Dict = field(default_factory=lambda: {
        "top_k": 2,
        "budget": 8,
        "cooldown_seconds": 2.0,
        "freeze": False,
        "max_parallel": 1
    })
    
    CRITICAL: Dict = field(default_factory=lambda: {
        "top_k": 1,
        "budget": 5,
        "cooldown_seconds": 5.0,
        "freeze": False,
        "max_parallel": 1
    })
    
    EMERGENCY: Dict = field(default_factory=lambda: {
        "top_k": 0,
        "budget": 0,
        "cooldown_seconds": 60.0,
        "freeze": True,
        "max_parallel": 0
    })


class AdaptiveRetrievalPolicy:
    """
    Dynamic retrieval policy engine.
    
    Replaces fixed top_k=3 with pressure-zone adaptive retrieval.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.policy = RetrievalPolicy()
        self.history: List[Dict] = []
        self.retrieval_log = []
        
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str):
        """Load custom policy configuration."""
        try:
            with open(config_path, 'r') as f:
                custom_policy = f.read()
            # Would parse and merge with defaults in production
        except FileNotFoundError:
            pass
    
    def get_policy_for_zone(self, pressure_zone: PressureZone) -> Dict:
        """
        Get retrieval policy for current pressure zone.
        """
        return getattr(self.policy, pressure_zone.value.upper(), self.policy.EARLY_CONTROL)
    
    def calculate_pressure_zone(self, context_usage: float, gpu_usage: float,
                               vram_usage: float = 0.0) -> PressureZone:
        """
        Calculate current pressure zone based on system metrics.
        
        Decision tree:
        1. Check for emergency conditions (>95% GPU or >95% context)
        2. Check for critical conditions (>90% GPU or >85% context)
        3. Check for preemptive conditions (>85% GPU or >75% context)
        4. Check for early control (>80% GPU or >65% context)
        5. Default to safe
        """
        # Emergency: system at risk
        if gpu_usage > 0.95 or context_usage > 0.95:
            return PressureZone.EMERGENCY
        
        # Critical: aggressive intervention needed
        if gpu_usage > 0.90 or context_usage > 0.85:
            return PressureZone.CRITICAL
        
        # Preemptive: prepare for potential issues
        if gpu_usage > 0.85 or context_usage > 0.75:
            return PressureZone.PREEMPTIVE
        
        # Early control: monitor closely
        if gpu_usage > 0.80 or context_usage > 0.65:
            return PressureZone.EARLY_CONTROL
        
        # Safe: normal operations
        return PressureZone.SAFE
    
    def get_adaptive_top_k(self, pressure_zone: Optional[PressureZone] = None,
                          context_usage: Optional[float] = None,
                          gpu_usage: Optional[float] = None) -> Tuple[int, str]:
        """
        Get adaptive top_k based on current pressure state.
        
        Returns: (top_k, reason)
        """
        if pressure_zone is None:
            if context_usage is None or gpu_usage is None:
                return 3, "Unknown pressure state"
            
            pressure_zone = self.calculate_pressure_zone(context_usage, gpu_usage)
        
        policy = self.get_policy_for_zone(pressure_zone)
        top_k = policy["top_k"]
        freeze = policy["freeze"]
        
        if freeze:
            return 0, f"Retrieval frozen: {pressure_zone.value}"
        
        return top_k, f"Pressure zone: {pressure_zone.value}"
    
    def get_dynamic_budget(self, pressure_zone: Optional[PressureZone] = None,
                          agent_ids: Optional[List[str]] = None) -> Tuple[float, int]:
        """
        Calculate dynamic retrieval budget.
        
        Implements shared retrieval budget pool:
        - global retrieval budget = 12
        - @intel consumes 5
        - @ops consumes 3
        - @comms consumes 1
        - reserve buffer = 3
        
        Adjusts based on pressure zone and agent demands.
        """
        if pressure_zone is None:
            return 12.0, 3  # Default: full budget, 3 agents
        
        base_budget = {
            PressureZone.SAFE: 12.0,
            PressureZone.EARLY_CONTROL: 10.0,
            PressureZone.PREEMPTIVE: 8.0,
            PressureZone.CRITICAL: 5.0,
            PressureZone.EMERGENCY: 0.0
        }.get(pressure_zone, 12.0)
        
        # Adjust for number of agents
        num_agents = len(agent_ids) if agent_ids else 3
        budget_per_agent = base_budget / max(num_agents, 1)
        
        return base_budget, num_agents
    
    def apply_cooldown(self, last_retrieval_time: float, pressure_zone: PressureZone) -> bool:
        """
        Check if enough time has passed since last retrieval.
        
        Returns: True if retrieval allowed, False if cooldown active
        """
        policy = self.get_policy_for_zone(pressure_zone)
        cooldown = policy["cooldown_seconds"]
        
        if last_retrieval_time is None:
            return True  # No prior retrieval
        
        elapsed = time.time() - last_retrieval_time
        return elapsed >= cooldown
    
    def should_freeze_retrieval(self, pressure_zone: PressureZone) -> bool:
        """
        Check if retrieval should be frozen.
        
        Only frozen in EMERGENCY zone.
        """
        policy = self.get_policy_for_zone(pressure_zone)
        return policy["freeze"]
    
    def calculate_pressure_zone_from_metrics(self, metrics: Dict) -> PressureZone:
        """
        Calculate pressure zone from metrics dictionary.
        """
        context_usage = metrics.get("context_usage", 0.0)
        gpu_usage = metrics.get("gpu_usage", 0.0)
        vram_usage = metrics.get("vram_usage", 0.0)
        
        return self.calculate_pressure_zone(context_usage, gpu_usage, vram_usage)


# Usage examples
def demo_adaptive_retrieval():
    """Demonstrate adaptive retrieval policy."""
    policy = AdaptiveRetrievalPolicy()
    
    # Test different pressure zones
    test_cases = [
        (0.50, 0.65, "Normal operation"),
        (0.72, 0.78, "Early control"),
        (0.82, 0.88, "Preemptive"),
        (0.90, 0.92, "Critical"),
        (0.95, 0.97, "Emergency")
    ]
    
    for context, gpu, description in test_cases:
        pressure = policy.calculate_pressure_zone(context, gpu)
        top_k, reason = policy.get_adaptive_top_k(pressure)
        budget, agents = policy.get_dynamic_budget(pressure)
        
        print(f"\n{description}")
        print(f"  Context: {context:.2f}, GPU: {gpu:.2f}")
        print(f"  Pressure Zone: {pressure.value}")
        print(f"  Adaptive top_k: {top_k}")
        print(f"  Reason: {reason}")
        print(f"  Dynamic budget: {budget:.1f}")
        
        if not policy.should_freeze_retrieval(pressure):
            print(f"  Cooldown: {policy.get_policy_for_zone(pressure)['cooldown_seconds']:.1f}s")
        else:
            print(f"  Cooldown: RETRIEVAL FROZEN")


if __name__ == "__main__":
    demo_adaptive_retrieval()
