#!/usr/bin/env python3
"""
Test suite for Context Pruner (Phase 6)
"""

import pytest
from tools.context_pruner import ContextPruner


class TestContextPruner:
    """Test Context Pruner functionality."""
    
    def test_prune_dead_context(self):
        """Pruner removes dead entries."""
        pruner = ContextPruner()
        context = {
            "tool1": {"status": "active", "tri": 0.9},
            "dead1": {"status": "dead"},
            "tool2": {"status": "active"}
        }
        optimized = pruner.prune_context(context)
        
        # Check dead entry removed
        assert "dead1" not in optimized
    
    def test_analyze_idle_occupancy(self):
        """Occupancy calculation."""
        pruner = ContextPruner()
        context = {
            "active1": {"status": "active"},
            "dead1": {"status": "dead"},
            "active2": {"status": "active"}
        }
        occupancy = pruner.analyze_idle_occupancy(context)
        # 2 active out of 3 total
        assert occupancy == 2/3
    
    def test_optimize_full(self):
        """Full optimization."""
        pruner = ContextPruner()
        context = {
            "tool1": {"status": "active", "tri": 0.9},
            "dead1": {"status": "dead"},
            "tool2": {"status": "active", "tri": 0.5}
        }
        optimized = pruner.optimize(context)
        
        # Check dead removed
        assert "dead1" not in optimized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
