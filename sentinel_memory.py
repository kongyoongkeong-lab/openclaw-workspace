"""
Sentinel Memory Learner - SELF-IMPROVING CORE
=================================================
ROLE: Memory optimizer + system intelligence governor

Features:
- Scan memory every 5 minutes
- Detect: repeated errors, repeated prompts, system inefficiency
- Generate improvement suggestions
- Auto-write insights into semantic memory
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import hashlib


class SentinelMemoryLearner:
    """
    Sentinel agent that learns from memory patterns and suggests improvements.
    """
    
    def __init__(self, memory_dir: str = "/home/jason2ykk/.openclaw/workspace"):
        self.memory_dir = Path(memory_dir)
        self.episodic_path = self.memory_dir / "episodic.jsonl"
        self.semantic_path = self.memory_dir / "semantic.jsonl"
        self.scan_interval_seconds = 300  # 5 minutes
        self.error_threshold = 3  # errors before flagging
        self.prompt_threshold = 5  # repeated prompts before flagging
        self.inefficiency_threshold = 2  # redundant ops before flagging
        
    def scan_memory(self) -> Dict[str, Any]:
        """
        Scan memory every 5 minutes and detect patterns.
        """
        scan_time = datetime.now()
        insights = {
            "scan_time": scan_time.isoformat(),
            "patterns_detected": [],
            "insights": [],
            "recommendations": []
        }
        
        # Load episodic memory
        episodic_events = self._load_jsonl(self.episodic_path)
        
        # Detect patterns
        patterns = self._detect_patterns(episodic_events, scan_time)
        
        # Generate insights
        insights["patterns_detected"] = patterns
        
        # Generate improvement suggestions
        insights["insights"] = self._generate_insights(patterns, episodic_events)
        
        # Generate recommendations
        insights["recommendations"] = self._generate_recommendations(patterns, insights["insights"])
        
        return insights
    
    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load JSONL file into list of dictionaries."""
        if not path.exists():
            return []
        
        events = []
        with open(path, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events
    
    def _detect_patterns(self, events: List[Dict[str, Any]], scan_time: datetime) -> List[Dict[str, Any]]:
        """
        Detect:
        - repeated errors
        - repeated prompts  
        - system inefficiency
        """
        patterns = []
        
        # 1. Detect repeated errors
        error_patterns = self._detect_repeated_errors(events)
        if error_patterns:
            patterns.append({
                "type": "repeated_errors",
                "count": len(error_patterns),
                "details": error_patterns[:5]  # Top 5 most frequent
            })
        
        # 2. Detect repeated prompts
        prompt_patterns = self._detect_repeated_prompts(events)
        if prompt_patterns:
            patterns.append({
                "type": "repeated_prompts",
                "count": len(prompt_patterns),
                "details": prompt_patterns[:5]
            })
        
        # 3. Detect system inefficiency (redundant operations)
        inefficiency_patterns = self._detect_system_inefficiency(events)
        if inefficiency_patterns:
            patterns.append({
                "type": "system_inefficiency",
                "count": len(inefficiency_patterns),
                "details": inefficiency_patterns[:5]
            })
        
        return patterns
    
    def _detect_repeated_errors(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repeated error patterns."""
        error_groups = {}
        
        for event in events:
            if "error" in event.get("type", "").lower() or "fail" in event.get("status", "").lower():
                error_key = event.get("error", event.get("message", event.get("type", "unknown")))
                
                if error_key not in error_groups:
                    error_groups[error_key] = {
                        "error": error_key,
                        "count": 0,
                        "examples": [],
                        "last_seen": None,
                        "contexts": set()
                    }
                
                error_groups[error_key]["count"] += 1
                if error_groups[error_key]["count"] <= 3:
                    error_groups[error_key]["examples"].append({
                        "timestamp": event.get("timestamp"),
                        "context": str(event.get("context", event.get("type", "")))
                    })
                else:
                    # Keep only the most recent examples
                    error_groups[error_key]["examples"].append({
                        "timestamp": event.get("timestamp"),
                        "context": str(event.get("context", event.get("type", "")))
                    })
                    error_groups[error_key]["examples"] = error_groups[error_key]["examples"][-3:]
                
                # Track unique contexts
                context_str = str(event.get("context", event.get("type", "")))
                error_groups[error_key]["contexts"].add(context_str)
                error_groups[error_key]["last_seen"] = event.get("timestamp")
        
        # Filter by threshold
        repeated_errors = [
            {
                "error": info["error"],
                "count": info["count"],
                "contexts": list(info["contexts"]),
                "examples": info["examples"]
            }
            for info in error_groups.values()
            if info["count"] >= self.error_threshold
        ]
        
        return sorted(repeated_errors, key=lambda x: x["count"], reverse=True)
    
    def _detect_repeated_prompts(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect repeated prompt patterns."""
        prompt_groups = {}
        
        for event in events:
            prompt = event.get("message", event.get("input", event.get("type", "")))
            if prompt:
                prompt_normalized = prompt.strip().lower()
                
                if prompt_normalized not in prompt_groups:
                    prompt_groups[prompt_normalized] = {
                        "prompt": prompt,
                        "count": 0,
                        "variations": set(),
                        "first_seen": event.get("timestamp"),
                        "last_seen": event.get("timestamp")
                    }
                
                prompt_groups[prompt_normalized]["count"] += 1
                prompt_groups[prompt_normalized]["variations"].add(
                    event.get("message", event.get("input", ""))
                )
                prompt_groups[prompt_normalized]["last_seen"] = event.get("timestamp")
        
        # Filter by threshold
        repeated_prompts = [
            {
                "prompt": info["prompt"],
                "count": info["count"],
                "variations": list(info["variations"])
            }
            for info in prompt_groups.values()
            if info["count"] >= self.prompt_threshold
        ]
        
        return sorted(repeated_prompts, key=lambda x: x["count"], reverse=True)
    
    def _detect_system_inefficiency(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect system inefficiency patterns."""
        inefficiency_patterns = {
            "duplicate_operations": [],
            "redundant_tool_calls": [],
            "wasted_retries": []
        }
        
        operation_history = {}
        
        for event in events:
            tool = event.get("tool", event.get("tool_name", event.get("type", "")))
            if tool:
                op_key = str(event.get("action", event.get("message", "")))
                
                if op_key not in operation_history:
                    operation_history[op_key] = {
                        "tool": tool,
                        "operations": [],
                        "first_seen": event.get("timestamp")
                    }
                
                operation_history[op_key]["operations"].append(event.get("timestamp"))
                operation_history[op_key]["count"] = len(operation_history[op_key]["operations"])
                
                # Check for duplicate operations within 1 minute
                if len(operation_history[op_key]["operations"]) >= 2:
                    timestamps = [
                        datetime.fromisoformat(ts) 
                        for ts in operation_history[op_key]["operations"][-2:]
                        if ts
                    ]
                    if timestamps:
                        time_diff = abs((timestamps[-1] - timestamps[-2]).total_seconds())
                        if time_diff <= 60 and operation_history[op_key]["count"] >= self.inefficiency_threshold:
                            if operation_history[op_key]["tool"] not in inefficiency_patterns["duplicate_operations"]:
                                inefficiency_patterns["duplicate_operations"].append({
                                    "tool": operation_history[op_key]["tool"],
                                    "operation": op_key,
                                    "count": operation_history[op_key]["count"],
                                    "pattern": "repeated_within_1_minute"
                                })
        
        return list(inefficiency_patterns.values())
    
    def _generate_insights(self, patterns: List[Dict[str, Any]], events: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement insights based on detected patterns."""
        insights = []
        
        for pattern in patterns:
            if pattern["type"] == "repeated_errors":
                for error_info in pattern["details"]:
                    insights.append(
                        f"🚨 RECURRENT ERROR DETECTED: '{error_info['error']}' "
                        f"has occurred {error_info['count']} times. "
                        f"Contexts observed: {', '.join(error_info['contexts'][:3])}"
                    )
            
            elif pattern["type"] == "repeated_prompts":
                for prompt_info in pattern["details"]:
                    insights.append(
                        f"📢 REPETITIVE PATTERN: User prompt '{prompt_info['prompt'][:80]}...' "
                        f"asked {prompt_info['count']} times. "
                        f"Consider improving documentation or providing clearer answers."
                    )
            
            elif pattern["type"] == "system_inefficiency":
                for ineff_info in pattern["details"]:
                    insights.append(
                        f"⚡ EFFICIENCY ALERT: {ineff_info.get('count', 'unknown')} duplicate/redundant operations "
                        f"detected in '{ineff_info.get('tool', 'unknown')}'."
                    )
        
        return insights
    
    def _generate_recommendations(self, patterns: List[Dict[str, Any]], insights: List[str]) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        for pattern in patterns:
            if pattern["type"] == "repeated_errors":
                for error_info in pattern["details"][:1]:  # Top error only
                    recommendations.append(
                        f"✅ FIX: Address recurring error '{error_info['error']}' by: "
                        f"1. Checking error logs 2. Implementing error handling 3. "
                        f"Adding retry logic with exponential backoff"
                    )
            
            elif pattern["type"] == "repeated_prompts":
                for prompt_info in pattern["details"][:1]:  # Top prompt only
                    recommendations.append(
                        f"💡 OPTIMIZE: For repeated prompt '{prompt_info['prompt'][:50]}...', "
                        f"consider: 1. Creating a helpful guide 2. Updating documentation 3. "
                        f"Adding quick-start examples"
                    )
            
            elif pattern["type"] == "system_inefficiency":
                recommendations.append(
                    "⚙️ OPTIMIZE: Reduce redundant operations by caching results, "
                    f"implementing rate limiting, or batching operations."
                )
        
        return recommendations
    
    def generate_insight_report(self, insights: Optional[Dict[str, Any]] = None) -> str:
        """Generate a human-readable insight report."""
        if insights is None:
            insights = self.scan_memory()
        
        report = []
        report.append("=" * 60)
        report.append("🔍 SENTINEL MEMORY LEARNER - INSIGHT REPORT")
        report.append("=" * 60)
        report.append(f"\n📅 Scan Time: {insights['scan_time']}")
        report.append(f"📊 Events Analyzed: {len(self._load_jsonl(self.episodic_path))}")
        
        if insights['patterns_detected']:
            report.append(f"\n⚠️  PATTERN DETECTIONS: {len(insights['patterns_detected'])}")
            for i, pattern in enumerate(insights['patterns_detected'], 1):
                report.append(f"\n  Pattern {i}: {pattern['type'].replace('_', ' ').title()}")
                report.append(f"    Count: {pattern['count']}")
                if 'details' in pattern and pattern['details']:
                    detail = pattern['details'][0]
                    report.append(f"    Example: {str(detail)[:150]}...")
        
        if insights['insights']:
            report.append(f"\n🧠 INSIGHTS: {len(insights['insights'])}")
            for insight in insights['insights'][:10]:  # Top 10
                report.append(f"  - {insight}")
        
        if insights['recommendations']:
            report.append(f"\n💡 RECOMMENDATIONS: {len(insights['recommendations'])}")
            for rec in insights['recommendations'][:5]:  # Top 5
                report.append(f"  - {rec}")
        
        report.append("\n" + "=" * 60)
        report.append("END OF REPORT")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def write_to_semantic_memory(self, insight: str) -> bool:
        """
        Auto-write insights into semantic memory (immutable).
        Returns True if successful, False otherwise.
        """
        if not self.semantic_path.exists():
            self.semantic_path.touch()
        
        # Create immutable hash for this insight
        insight_hash = hashlib.sha256(insight.encode()).hexdigest()[:16]
        
        # Create semantic memory entry
        entry = {
            "type": "sentinel_insight",
            "timestamp": datetime.now().isoformat(),
            "hash": insight_hash,
            "content": insight,
            "source": "sentinel_memory_liner"
        }
        
        # Append to semantic memory JSONL
        with open(self.semantic_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")
        
        return True
    
    def continuous_monitor(self, mode: str = "background") -> None:
        """
        Run continuous memory monitoring.
        mode: "background" for daemon-like operation, "single" for one scan
        """
        if mode == "single":
            insights = self.scan_memory()
            print(self.generate_insight_report(insights))
            return
        
        # Background monitoring
        print(f"🛡️  Sentinel Memory Learner started in {mode} mode")
        print(f"⏱️  Scanning interval: {self.scan_interval_seconds} seconds")
        print(f"🔄 Press Ctrl+C to stop\n")
        
        try:
            while True:
                print(f"\n📊 Scanning memory... {datetime.now().strftime('%H:%M:%S')}")
                insights = self.scan_memory()
                
                # Generate and save report
                report = self.generate_insight_report(insights)
                print(report)
                
                # Write critical insights to semantic memory
                for insight in insights.get('insights', []):
                    if any(kw in insight.lower() for kw in ['error', 'alert', 'optimize']):
                        self.write_to_semantic_memory(insight)
                
                # Wait for next scan
                time.sleep(self.scan_interval_seconds)
                
        except KeyboardInterrupt:
            print("\n🛑 Sentinel Memory Learner stopped by user")


# Convenience functions for external use
def analyze_memory_trends(memory_dir: str = "/home/jason2ykk/.openclaw/workspace") -> Dict[str, Any]:
    """Analyze memory trends using Sentinel."""
    sentinel = SentinelMemoryLearner(memory_dir)
    return sentinel.scan_memory()


def generate_insight_report(memory_dir: str = "/home/jason2ykk/.openclaw/workspace") -> str:
    """Generate a memory insight report."""
    sentinel = SentinelMemoryLearner(memory_dir)
    return sentinel.generate_insight_report()


# Example usage
if __name__ == "__main__":
    sentinel = SentinelMemoryLearner()
    
    # Single scan
    print("=== Single Scan ===")
    print(sentinel.generate_insight_report())
    
    # Continuous monitoring (demo mode - 10 second intervals for testing)
    # Uncomment to run
    # sentinel.continuous_monitor(mode="background")