#!/usr/bin/env python3
"""
SPG - System Pressure Governor

Provides pressure gating for Pentagon agents.

Zones:
- SAFE (< 0.55): Normal operation
- EARLY (0.55-0.70): Monitor mode
- THROTTLE (0.70-0.80): Single-threaded, slow ops
- CRITICAL (0.80-0.90): Write with delays
- EMERGENCY (>= 0.90): Read-only mode
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional


class PressureData:
    """Pressure data container."""
    
    def __init__(self, pressure_index: float, timestamp: float):
        self.pressure_index = pressure_index
        self.timestamp = timestamp
        self.zone = self._get_zone(pressure_index)
    
    def _get_zone(self, index: float) -> str:
        """Get pressure zone."""
        if index <= 0.55:
            return "SAFE"
        elif index <= 0.70:
            return "EARLY"
        elif index <= 0.80:
            return "THROTTLE"
        elif index <= 0.90:
            return "CRITICAL"
        else:
            return "EMERGENCY"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pressure_index": self.pressure_index,
            "timestamp": self.timestamp,
            "zone": self.zone,
        }


class SPGGovernor:
    """
    System Pressure Governor.
    
    Calculates pressure based on:
    1. Memory backlog size
    2. Recent operations
    3. System load
    """
    
    def __init__(self, workspace: str = None):
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self._pressure_data = None
        self._last_update = None
        self._episodic_path = self.workspace / "episodic.jsonl"
        self._semantic_path = self.workspace / "semantic.jsonl"
    
    def get_pressure_signal(self) -> str:
        """Get current SPG pressure signal."""
        if self._pressure_data and self._last_update and time.time() - self._last_update < 60:
            return self._pressure_data.zone
        
        pressure_data = self.calculate_pressure()
        return pressure_data["zone"]
    
    def calculate_pressure(self) -> Dict[str, Any]:
        """Calculate current pressure index."""
        # Count episodic memory lines
        episodic_lines = 0
        if self._episodic_path.exists():
            with open(self._episodic_path) as f:
                episodic_lines = sum(1 for _ in f)
        
        # Count semantic memory lines
        semantic_lines = 0
        if self._semantic_path.exists():
            with open(self._semantic_path) as f:
                semantic_lines = sum(1 for _ in f)
        
        # Total pressure (combined memory backlog)
        total_lines = episodic_lines + semantic_lines
        
        # Normalize to 0-1 range
        # 3000 lines = 1.0 pressure
        pressure_index = min(total_lines / 3000, 1.0)
        
        # Update pressure data
        self._pressure_data = PressureData(pressure_index, time.time())
        self._last_update = time.time()
        
        return self._pressure_data.to_dict()
    
    def get_recommendation(self) -> str:
        """Get SPG recommendation."""
        zone = self.get_pressure_signal()
        
        recommendations = {
            "SAFE": "Normal operation. All capabilities available.",
            "EARLY": "Monitor system resources. Consider throttling background tasks.",
            "THROTTLE": "Single-threaded operations only. Avoid parallel execution.",
            "CRITICAL": "Write operations only. Delay non-critical tasks.",
            "EMERGENCY": "Read-only mode. No new writes or executions.",
        }
        
        return recommendations.get(zone, "Unknown zone")


def get_sp_governor(workspace: Optional[str] = None) -> SPGGovernor:
    """Get SPG governor instance."""
    return SPGGovernor(workspace=workspace)


# Test
if __name__ == "__main__":
    spg = get_sp_governor("/home/jason2ykk/.openclaw/workspace")
    signal = spg.get_pressure_signal()
    print(f"SPG Governor Initialized")
    print(f"Pressure Signal: {signal}")
    print(f"Recommendation: {spg.get_recommendation()}")
