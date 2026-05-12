#!/usr/bin/env python3
"""
Context Compression Module - LTM v1 with SPG Integration

Integrates with SPG pressure signals to trigger compression.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

class LTMCompressor:
    """
    Context compression module with SPG integration.
    
    Triggers compression when:
    1. Episodic memory >= 3000 lines (legacy)
    2. OR pressure index >= 0.70 (new)
    """
    
    THRESHOLD = 3000
    RATIO = 0.5  # 50% compression ratio
    
    def __init__(self, episodic_path: str = "episodic.jsonl"):
        self.path = Path(episodic_path)
        self.count = 0
    
    def check_compression_legacy(self) -> Dict[str, Any]:
        """Legacy check: lines >= threshold."""
        if not self.path.exists():
            return {"status": "no_file", "reason": "episodic.jsonl not found"}
        
        self.count = sum(1 for _ in open(self.path))
        return {
            "status": "checked",
            "lines": self.count,
            "threshold": self.THRESHOLD,
            "needs_compression": self.count >= self.THRESHOLD,
        }
    
    def check_compression_pressure(self, pressure_index: float) -> Dict[str, Any]:
        """Pressure-gated compression check."""
        zone = self._get_zone(pressure_index)
        
        # Trigger compression in THROTTLE+ zones
        if pressure_index >= 0.70:
            self.count = sum(1 for _ in open(self.path))
            return {
                "status": "pressure_triggered",
                "pressure_index": pressure_index,
                "zone": zone,
                "lines": self.count,
                "action": self._compress() if self.count >= self.THRESHOLD else "skipped_low_lines",
            }
        
        return {
            "status": "pressure_normal",
            "pressure_index": pressure_index,
            "zone": zone,
            "action": "monitor",
        }
    
    def _get_zone(self, pressure_index: float) -> str:
        """Get pressure zone."""
        if pressure_index <= 0.55:
            return "SAFE"
        elif pressure_index <= 0.70:
            return "EARLY"
        elif pressure_index <= 0.80:
            return "THROTTLE"
        elif pressure_index <= 0.90:
            return "CRITICAL"
        else:
            return "EMERGENCY"
    
    def _compress(self) -> Dict[str, Any]:
        """Execute compression."""
        if not self.path.exists():
            return {"status": "error", "reason": "no_file"}
        
        with open(self.path) as f:
            lines = f.readlines()
        
        keep = int(len(lines) * self.RATIO)
        compress = lines[keep:]
        
        # Write compressed lines to archive
        archive_path = self.path.parent / "compressed" / f"{self.path.stem}_old_{int(time.time())}.jsonl"
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Filter to keep only essential metadata
        compressed_lines = [line.replace('\n', '') for line in compress[:len(compress) * self.RATIO]]
        
        with open(archive_path, 'w') as f:
            f.writelines(f"{line}\n" for line in compressed_lines)
        
        # Rewriting original file with only kept lines
        with open(self.path, 'w') as f:
            f.writelines(lines[:keep])
        
        return {
            "status": "compressed",
            "kept": keep,
            "archived": len(compressed_lines),
            "archive_path": archive_path,
        }
    
    def run_pressure_check(self, pressure_index: float) -> Dict[str, Any]:
        """Run pressure-gated compression check."""
        pressure_result = self.check_compression_pressure(pressure_index)
        
        # Legacy check if pressure normal
        if pressure_result["status"] == "pressure_normal":
            legacy_result = self.check_compression_legacy()
            if legacy_result.get("needs_compression"):
                return self._compress()
        
        return pressure_result
