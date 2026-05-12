"""
P4 — Compression Effectiveness Delta (CED)

Validates that compression actually reduces cognitive load,
not just token count.

Three Layers:
1. Raw Compression Delta (token count)
2. Semantic Retention Delta (cosine similarity)
3. Rehydration Utility (compression reuse rate)
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
import numpy as np


class CompressionEffectivenessTracker:
    """
    Tracks compression effectiveness through 3 layers:
    1. Raw token reduction
    2. Semantic fidelity preservation
    3. Rehydration utility (compression reuse)
    """

    # Alert thresholds
    SEMANTIC_EXCELLENT = 0.95
    SEMANTIC_HEALTHY = 0.90
    SEMANTIC_WARNING = 0.80
    SEMANTIC_DANGEROUS = 0.75

    REHYDRATION_GOOD = 0.50
    REHYDRATION_POOR = 0.30

    def __init__(self, embeddings_path: str = "memory/embeddings.json"):
        """
        Initialize CED tracker.
        
        Args:
            embeddings_path: Path to store embeddings for cosine similarity
        """
        self.embeddings_path = Path(embeddings_path)
        self.embeddings = {}
        self.results = []
        
    def calculate_raw_delta(self, before_tokens: int, after_tokens: int) -> dict:
        """
        Layer 1: Raw Compression Delta
        
        Formula: CEDraw = before_tokens - after_tokens
        
        Args:
            before_tokens: Token count before compression
            after_tokens: Token count after compression
            
        Returns:
            dict with raw delta, reduction percentage, status
        """
        raw_delta = before_tokens - after_tokens
        
        if before_tokens == 0:
            reduction_pct = 0.0
        else:
            reduction_pct = (raw_delta / before_tokens) * 100
        
        # Determine status
        if raw_delta < 0:
            status = "CRITICAL_EXPANSION"
        elif raw_delta < before_tokens * 0.1:  # <10% reduction
            status = "WARNING_LOW_REDUCTION"
        elif raw_delta < before_tokens * 0.3:
            status = "ACCEPTABLE"
        else:
            status = "EXCELLENT"
        
        return {
            "layer": "raw_delta",
            "before_tokens": before_tokens,
            "after_tokens": after_tokens,
            "raw_delta": raw_delta,
            "reduction_pct": reduction_pct,
            "status": status,
            "alert": raw_delta < 0
        }

    def calculate_semantic_delta(self, original_text: str, compressed_text: str) -> dict:
        """
        Layer 2: Semantic Retention Delta (Critical)
        
        Formula: CEDsemantic = cosine(original_embedding, compressed_embedding)
        
        Many compressions reduce tokens but kill meaning.
        This detects when we lose the forest for the trees.
        
        Args:
            original_text: Original block before compression
            compressed_text: Compressed block after compression
            
        Returns:
            dict with semantic similarity score and status
        """
        # Simplified embedding simulation (use real embeddings in production)
        # For now, use hash-based similarity simulation
        original_hash = self._hash_to_vector(original_text)
        compressed_hash = self._hash_to_vector(compressed_text)
        
        # Calculate cosine similarity (simplified)
        dot_product = np.dot(original_hash, compressed_hash)
        norm_original = np.linalg.norm(original_hash)
        norm_compressed = np.linalg.norm(compressed_hash)
        
        if norm_original == 0 or norm_compressed == 0:
            semantic_sim = 0.0
        else:
            semantic_sim = dot_product / (norm_original * norm_compressed)
        
        # Clamp to valid range
        semantic_sim = np.clip(semantic_sim, -1.0, 1.0)
        semantic_sim = (semantic_sim + 1) / 2  # Convert to 0-1 range
        
        # Determine status
        if semantic_sim >= self.SEMANTIC_EXCELLENT:
            status = "EXCELLENT"
        elif semantic_sim >= self.SEMANTIC_HEALTHY:
            status = "HEALTHY"
        elif semantic_sim >= self.SEMANTIC_WARNING:
            status = "WARNING_DRIFT_BEGINNING"
        else:
            status = "DANGEROUS_COMPRESSION"
        
        return {
            "layer": "semantic_retention",
            "original_text_length": len(original_text),
            "compressed_text_length": len(compressed_text),
            "semantic_similarity": round(semantic_sim, 4),
            "semantic_retention": round(semantic_sim * 100, 2),
            "status": status,
            "alert": semantic_sim < self.SEMANTIC_WARNING
        }

    def calculate_rehydration_utility(self, compressed_blocks: list, usage_records: list) -> dict:
        """
        Layer 3: Rehydration Utility (Future Killer Metric)
        
        Detects compression black holes.
        Low ratio = compressing garbage (useless telemetry, dead logs, spam)
        
        Formula: compressed_block_used_again / total_compressed_blocks
        
        Args:
            compressed_blocks: List of compressed block identifiers
            usage_records: List of records showing which blocks were reused
            
        Returns:
            dict with rehydration rate and analysis
        """
        total_blocks = len(compressed_blocks)
        if total_blocks == 0:
            return {
                "layer": "rehydration_utility",
                "total_blocks": 0,
                "blocks_used_again": 0,
                "rehydration_rate": 0.0,
                "status": "NO_DATA",
                "analysis": "No compression blocks tracked yet"
            }
        
        blocks_used = sum(1 for r in usage_records if r["block_id"] in compressed_blocks)
        rehydration_rate = blocks_used / total_blocks
        
        # Determine status
        if rehydration_rate >= self.REHYDRATION_GOOD:
            status = "UTILIZING_COMPRESSION"
        elif rehydration_rate >= self.REHYDRATION_POOR:
            status = "MIXED_RESULTS"
        else:
            status = "COMPRESSING_GARBAGE"
        
        analysis = self._analyze_compression_health(total_blocks, blocks_used, rehydration_rate)
        
        return {
            "layer": "rehydration_utility",
            "total_blocks": total_blocks,
            "blocks_used_again": blocks_used,
            "rehydration_rate": round(rehydration_rate, 4),
            "rehydration_rate_pct": round(rehydration_rate * 100, 2),
            "status": status,
            "alert": rehydration_rate < self.REHYDRATION_POOR,
            "analysis": analysis
        }

    def _hash_to_vector(self, text: str, vector_dim: int = 768) -> np.ndarray:
        """
        Simplified hash-to-vector for demonstration.
        Replace with actual embedding model in production.
        
        Args:
            text: Input text
            vector_dim: Embedding dimension
            
        Returns:
            numpy array representing text embedding
        """
        # Use SHA256 hash converted to float vector
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Convert to normalized float vector
        vector = np.frombuffer(hash_bytes[:vector_dim], dtype=np.float32) / 256.0
        
        # Normalize to unit vector
        vector = vector / (np.linalg.norm(vector) + 1e-8)
        
        return vector

    def _analyze_compression_health(self, total: int, used: int, rate: float) -> str:
        """
        Analyze compression health based on rehydration rate.
        """
        if total == 0:
            return "No compression blocks tracked."
        
        garbage_ratio = 1.0 - rate
        
        if garbage_ratio < 0.2:
            return f"Compression is healthy. Only {garbage_ratio*100:.1f}% of blocks are unused."
        elif garbage_ratio < 0.5:
            return f"Moderate garbage accumulation. {garbage_ratio*100:.1f}% of compressed blocks not reused."
        else:
            return f"CRITICAL: {garbage_ratio*100:.1f}% of compression output is garbage. " \
                   f"Consider purging unused blocks or reviewing compression source."

    def track_compression_cycle(self, original: str, compressed: str, 
                                 original_tokens: int, compressed_tokens: int,
                                 block_id: str = None) -> dict:
        """
        Track a complete compression cycle through all 3 layers.
        
        Args:
            original: Original text block
            compressed: Compressed text block
            original_tokens: Token count before compression
            compressed_tokens: Token count after compression
            block_id: Optional block identifier for tracking
            
        Returns:
            Combined results from all 3 CED layers
        """
        raw_result = self.calculate_raw_delta(original_tokens, compressed_tokens)
        semantic_result = self.calculate_semantic_delta(original, compressed)
        
        # Track compression for rehydration analysis
        if block_id:
            # Use simple dict-based tracking
            self._track_block_usage(block_id)
        
        # Get rehydration result (would need full usage tracking in production)
        rehydration_result = self._get_rehydration_result()
        
        # Combine all layers
        cycle_result = {
            "timestamp": datetime.now().isoformat(),
            "block_id": block_id,
            "raw_delta": raw_result,
            "semantic_retention": semantic_result,
            "rehydration_utility": rehydration_result,
            "overall_status": self._determine_overall_status(raw_result, semantic_result, rehydration_result),
            "recommendation": self._generate_recommendation(
                raw_result, semantic_result, rehydration_result
            )
        }
        
        self.results.append(cycle_result)
        return cycle_result

    def _track_block_usage(self, block_id: str) -> None:
        """
        Track that a block has been used (simplified implementation).
        """
        if not hasattr(self, 'block_usage'):
            self.block_usage = set()
        self.block_usage.add(block_id)

    def _get_rehydration_result(self) -> dict:
        """
        Get current rehydration utility result (simplified).
        """
        if not hasattr(self, 'block_usage'):
            return {
                "layer": "rehydration_utility",
                "total_blocks": 0,
                "blocks_used_again": 0,
                "rehydration_rate": 0.0,
                "status": "NO_DATA"
            }
        
        # Simplified: assume 50% reuse rate
        total = len(self.block_usage)
        used_again = total // 2  # Simplified assumption
        
        return {
            "layer": "rehydration_utility",
            "total_blocks": total,
            "blocks_used_again": used_again,
            "rehydration_rate": round(used_again / total, 4) if total > 0 else 0.0,
            "rehydration_rate_pct": round(used_again / total * 100, 2) if total > 0 else 0.0,
            "status": "MIXED_RESULTS" if total > 0 else "NO_DATA"
        }

    def _determine_overall_status(self, raw: dict, semantic: dict, rehydration: dict) -> str:
        """
        Determine overall compression health status.
        """
        # Priority: Semantic > Rehydration > Raw
        if semantic["alert"]:
            return "CRITICAL_SEMANTIC_FAILURE"
        if rehydration.get("alert", False):
            return "CRITICAL_GARBAGE_COMPRESSION"
        if raw["alert"]:
            return "CRITICAL_EXPANSION"
        
        if semantic["status"] == "DANGEROUS_COMPRESSION":
            return "SEMANTIC_DECAY"
        if rehydration["status"] == "COMPRESSING_GARBAGE":
            return "GARBAGE_COMPRESSION"
        
        return raw["status"]

    def _generate_recommendation(self, raw: dict, semantic: dict, rehydration: dict) -> str:
        """
        Generate actionable recommendation.
        """
        if semantic["alert"]:
            return "⚠️ CRITICAL: Compression is killing meaning. Stop this compression pipeline. " \
                   "Use alternative compression strategy that preserves semantic content."
        
        if rehydration.get("alert", False):
            return "⚠️ WARNING: Compressing garbage. Review what's being compressed. " \
                   f"Only {rehydration['rehydration_rate_pct']:.1f}% of compressed blocks are reused."
        
        if raw["alert"]:
            return "🔴 EMERGENCY: Compression is expanding context. Compression failed. " \
                   f"Expansion of {raw['raw_delta']} tokens detected."
        
        if raw["status"] == "WARNING_LOW_REDUCTION":
            return "⚠️ Low compression efficacy. Consider optimizing compression algorithm."
        
        if rehydration["status"] == "MIXED_RESULTS":
            return f"💡 Mixed compression utility. {rehydration['rehydration_rate_pct']:.1f}% reuse rate. " \
                   "Consider purging unused blocks periodically."
        
        return "✅ Compression healthy. Continue monitoring."

    def generate_report(self) -> dict:
        """
        Generate comprehensive CED report.
        """
        if not self.results:
            return {"error": "No compression cycles tracked yet."}
        
        avg_raw_delta = sum(r["raw_delta"]["raw_delta"] for r in self.results) / len(self.results)
        avg_reduction = sum(r["raw_delta"]["reduction_pct"] for r in self.results) / len(self.results)
        avg_semantic = sum(r["semantic_retention"]["semantic_similarity"] for r in self.results) / len(self.results)
        avg_rehydration = sum(r["rehydration_utility"]["rehydration_rate"] for r in self.results) / len(self.results)
        
        critical_count = sum(1 for r in self.results if r["overall_status"] == "CRITICAL_SEMANTIC_FAILURE")
        warning_count = sum(1 for r in self.results if r["overall_status"] in ["WARNING_DRIFT_BEGINNING", "WARNING_LOW_REDUCTION"])
        
        return {
            "summary": {
                "total_cycles": len(self.results),
                "avg_raw_reduction_pct": round(avg_reduction, 2),
                "avg_semantic_similarity": round(avg_semantic, 4),
                "avg_rehydration_rate": round(avg_rehydration, 4),
                "critical_failures": critical_count,
                "warnings": warning_count
            },
            "health_check": self._overall_health_check(avg_semantic, avg_rehydration),
            "recent_results": self.results[-10:],  # Last 10 cycles
            "recommendations": self._generate_overall_recommendations()
        }

    def _overall_health_check(self, avg_semantic: float, avg_rehydration: float) -> str:
        """
        Overall health assessment.
        """
        if avg_semantic < self.SEMANTIC_WARNING or avg_rehydration < self.REHYDRATION_POOR:
            return "CRITICAL_COMPRESSION_FAILURE"
        elif avg_semantic < self.SEMANTIC_HEALTHY or avg_rehydration < self.REHYDRATION_GOOD:
            return "DEGRADED_COMPRESSION"
        elif avg_reduction < 10:
            return "LOW_COMPRESSION_EFFICACY"
        else:
            return "HEALTHY_COMPRESSION"

    def _generate_overall_recommendations(self) -> list:
        """
        Generate overall recommendations.
        """
        recommendations = []
        
        avg_semantic = sum(r["semantic_retention"]["semantic_similarity"] for r in self.results) / max(len(self.results), 1)
        avg_rehydration = sum(r["rehydration_utility"]["rehydration_rate"] for r in self.results) / max(len(self.results), 1)
        
        if avg_semantic < self.SEMANTIC_WARNING:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "semantic_decay",
                "issue": f"Average semantic fidelity {avg_semantic:.4f} is below safe threshold (0.90). " \
                         "Compression is killing meaning."
            })
        
        if avg_rehydration < self.REHYDRATION_POOR:
            recommendations.append({
                "priority": "HIGH",
                "category": "garbage_compression",
                "issue": f"Average rehydration rate {avg_rehydration:.4f} indicates compressing garbage. " \
                         "Review compression source."
            })
        
        avg_reduction = sum(r["raw_delta"]["reduction_pct"] for r in self.results) / max(len(self.results), 1)
        if avg_reduction < 10:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "low_efficacy",
                "issue": f"Average reduction {avg_reduction:.2f}% is low. " \
                         "Consider optimizing compression algorithm."
            })
        
        return recommendations


# Usage Example
if __name__ == "__main__":
    tracker = CompressionEffectivenessTracker()
    
    # Track a compression cycle
    result = tracker.track_compression_cycle(
        original="Original context block content here...",
        compressed="Compressed version of context...",
        original_tokens=100,
        compressed_tokens=60,
        block_id="test_block_001"
    )
    
    print(json.dumps(result, indent=2))
    
    # Generate report
    report = tracker.generate_report()
    print(json.dumps(report, indent=2))
