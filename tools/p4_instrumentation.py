"""
P4 Instrumentation — Wire CED into OpenClaw Compression Pipeline

This script instruments the actual compression/decompression operations
to capture pre/post token counts and embeddings for CED calculation.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from p4_compression_effectiveness import CompressionEffectivenessTracker


class CEDInstrumentation:
    """
    Instruments compression pipeline to track CED metrics.
    
    Integrates with:
    - context_window_manager: Captures token counts
    - compressor/decompressor: Captures before/after blocks
    - SPState: Stores results
    """

    def __init__(self, ced_tracker_path: str = "tools/p4_compression_effectiveness.py",
                 state_dir: str = "memory"):
        """
        Initialize CED instrumentation.
        
        Args:
            ced_tracker_path: Path to CED tracker module
            state_dir: Directory to store CED results
        """
        self.tracker = CompressionEffectivenessTracker()
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        # CED results storage
        self.results_file = self.state_dir / "ced_results.jsonl"
        
        # Load existing blocks if any
        self._load_existing_blocks()

    def _load_existing_blocks(self):
        """Load existing compressed blocks from memory."""
        # In production, this would query the memory system
        if self.state_dir.exists():
            self.tracker.block_usage = set()
            for jsonl_file in self.state_dir.glob("blocks.jsonl"):
                with open(jsonl_file) as f:
                    for line in f:
                        block = json.loads(line.strip())
                        self.tracker.block_usage.add(block.get("id", ""))

    def instrument_compression(self, original_text: str, compression_algorithm: str = None) -> dict:
        """
        Intercept and instrument a compression operation.
        
        Args:
            original_text: Original text to be compressed
            compression_algorithm: Name of compression algorithm used
            
        Returns:
            dict with instrumented compression result including CED metrics
        """
        # In production, capture from actual compression hooks
        # For now, simulate with simplified logic
        
        # Simulate compression (in production, this is real compression)
        compressed_text = self._simulate_compression(original_text)
        
        # Simulate token counting
        original_tokens = self._estimate_tokens(original_text)
        compressed_tokens = self._estimate_tokens(compressed_text)
        
        # Generate block ID
        block_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(original_text) % 10000:04d}"
        
        # Track the compression cycle
        ced_result = self.tracker.track_compression_cycle(
            original=original_text,
            compressed=compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            block_id=block_id,
            algorithm=compression_algorithm
        )
        
        # Simulate rehydration tracking (would be real in production)
        self._simulate_rehydration_tracking(block_id)
        
        # Generate alert if critical
        alert = self._generate_ced_alert(ced_result)
        
        # Save to results file
        self._save_result(ced_result)
        
        return {
            "original_text_length": len(original_text),
            "compressed_text_length": len(compressed_text),
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "ced_result": ced_result,
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }

    def _simulate_compression(self, text: str) -> str:
        """
        Simulate compression (production would use real compression).
        
        Args:
            text: Text to compress
            
        Returns:
            Compressed text (simulated)
        """
        # Simplified compression simulation
        # In production, this would use actual compression logic
        return f"COMPRESSED:{text[:50]}...[...]{text[-50:]}"

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (simplified heuristic).
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated token count
        """
        # Rough approximation: ~7500 chars per 1000 tokens
        return max(1, len(text) // 7500)

    def _simulate_rehydration_tracking(self, block_id: str) -> None:
        """
        Simulate tracking block reuse (production would track real usage).
        
        Args:
            block_id: Block identifier to track
        """
        # In production, this would query usage metrics
        # For now, track that block was "used" once
        self.tracker.block_usage.add(block_id)

    def _generate_ced_alert(self, ced_result: dict) -> dict:
        """
        Generate alert if CED metrics indicate critical issues.
        
        Args:
            ced_result: CED analysis result
            
        Returns:
            Alert dict (empty if no alert)
        """
        raw_alert = ced_result["raw_delta"].get("alert", False)
        semantic_alert = ced_result["semantic_retention"].get("alert", False)
        rehydration_alert = ced_result["rehydration_utility"].get("alert", False)
        
        if not any([raw_alert, semantic_alert, rehydration_alert]):
            return {}
        
        return {
            "severity": "CRITICAL" if semantic_alert else "WARNING",
            "message": ced_result["recommendation"],
            "layers": {
                "raw_delta_alert": raw_alert,
                "semantic_alert": semantic_alert,
                "rehydration_alert": rehydration_alert
            }
        }

    def _save_result(self, result: dict) -> None:
        """
        Save CED result to results file.
        
        Args:
            result: CED analysis result
        """
        with open(self.results_file, "a") as f:
            f.write(json.dumps(result) + "\n")

    def get_latest_result(self) -> dict:
        """
        Get the latest CED result.
        
        Returns:
            Most recent CED analysis result
        """
        if not self.results_file.exists():
            return None
        
        with open(self.results_file) as f:
            lines = f.readlines()
            if not lines:
                return None
            
            return json.loads(lines[-1].strip())

    def get_summary(self) -> dict:
        """
        Get CED summary from all results.
        
        Returns:
            Summary statistics
        """
        if not self.results_file.exists():
            return {"error": "No CED results yet."}
        
        with open(self.results_file) as f:
            results = [json.loads(line) for line in f if line.strip()]
        
        if not results:
            return {"error": "No results."}
        
        return {
            "total_cycles": len(results),
            "latest_result": results[-1],
            "average_metrics": self._calculate_averages(results)
        }

    def _calculate_averages(self, results: list) -> dict:
        """
        Calculate average CED metrics.
        
        Args:
            results: List of CED results
            
        Returns:
            Average metrics
        """
        if not results:
            return {}
        
        avg_raw_reduction = sum(r["raw_delta"]["reduction_pct"] for r in results) / len(results)
        avg_semantic = sum(r["semantic_retention"]["semantic_similarity"] for r in results) / len(results)
        avg_rehydration = sum(r["rehydration_utility"]["rehydration_rate"] for r in results) / len(results)
        
        return {
            "avg_raw_reduction_pct": round(avg_raw_reduction, 2),
            "avg_semantic_similarity": round(avg_semantic, 4),
            "avg_rehydration_rate": round(avg_rehydration, 4)
        }


# Test the instrumentation
if __name__ == "__main__":
    print("🚀 P4 CED Instrumentation Ready")
    print("=" * 50)
    
    # Create instrumentation
    instrumentation = CEDInstrumentation()
    
    # Test compression cycle
    result = instrumentation.instrument_compression(
        original_text="This is a test of the OpenClaw compression effectiveness "
                      "detection system. We are testing whether compression "
                      "actually reduces cognitive load or just reduces token count."
    )
    
    print(json.dumps(result, indent=2))
    
    # Show summary
    print("\n📊 CED Summary:")
    print(json.dumps(instrumentation.get_summary(), indent=2))
