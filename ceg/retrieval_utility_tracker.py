#!/usr/bin/env python3
"""
Retrieval Usefulness Ratio (RUR) Runtime Tracker
Prevents retrieval inflation and tracks actual utility attribution
"""

from typing import Dict, List, Optional
from datetime import datetime

class RetrievalUtilityTracker:
    """
    Tracks retrieval utility attribution instead of just retrieval count.
    
    Key distinction:
    - retrieved only: ❌ doesn't count
    - briefly referenced: ⚠️ low utility
    - affected reasoning chain: ✅ medium utility  
    - affected final output: ✅✅ high utility
    """
    
    def __init__(self):
        self.retrieval_events = []
        self.uses = []
        self.discards = []
        self.total_retrievals = 0
        self.productive_retrievals = 0
        
    def record_retrieval(self, retrievals: List[str], context: Dict) -> Dict:
        """Record a retrieval event with utility attribution."""
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "retrieved": retrievals,
            "actually_referenced": [],  # Will be updated
            "used_in_final_output": [],  # Will be updated
            "utility_level": "unknown",  # Will be updated
            "context": context,
        }
        
        self.retrieval_events.append(event)
        self.total_retrievals += len(retrievals)
        
        return event
    
    def mark_referenced(self, event_id: int, referenced: List[str]):
        """Mark which retrievals were actually referenced."""
        for event in self.retrieval_events:
            if event["id"] == event_id:
                event["actually_referenced"] = referenced
                break
    
    def mark_used_in_output(self, event_id: int, used_in_output: List[str]):
        """Mark which retrievals affected final output."""
        for event in self.retrieval_events:
            if event["id"] == event_id:
                event["used_in_final_output"] = used_in_output
                event["utility_level"] = "HIGH" if used_in_output else "MEDIUM"
                break
    
    def calculate_rur(self) -> float:
        """Calculate Retrieval Usefulness Ratio."""
        if self.total_retrievals == 0:
            return 0.0
        
        # Productive = affected final output OR significantly affected reasoning
        productive_count = sum(
            1 for e in self.retrieval_events 
            if e.get("used_in_final_output")
        )
        
        return productive_count / self.total_retrievals
    
    def get_utility_distribution(self) -> Dict[str, int]:
        """Get distribution of retrieval utility levels."""
        dist = {
            "none": 0,  # Retrieved only
            "low": 0,   # Briefly referenced
            "medium": 0, # Affected reasoning
            "high": 0,  # Affected final output
        }
        
        for event in self.retrieval_events:
            if event.get("used_in_final_output"):
                dist["high"] += len(event["used_in_final_output"])
            elif event.get("actually_referenced"):
                dist["low"] += len(event["actually_referenced"])
        
        return dist
    
    def get_retrieval_inflation_score(self) -> float:
        """
        Calculate inflation score: how much retrieval activity doesn't lead to utility.
        
        Returns 0-1 where:
        - 0 = healthy (all retrievals are useful)
        - 1 = extreme inflation (no retrievals are useful)
        """
        dist = self.get_utility_distribution()
        total = sum(dist.values())
        
        if total == 0:
            return 0.0
        
        inflation = (dist["none"] + dist["low"]) / total
        return inflation

# ========= RUNTIME INSTRUMENTATION =========
class RetrievalInstrumentation:
    """Runtime instrumentation for @intel agent."""
    
    def __init__(self):
        self.tracker = RetrievalUtilityTracker()
        
    def instrument_retrieval_flow(self, retrieval_result: Dict) -> Dict:
        """
        Instrument retrieval flow with utility tracking.
        
        Before returning, mark which retrievals were actually used.
        """
        context = retrieval_result.get("context", {})
        retrievals = retrieval_result.get("retrievals", [])
        
        # Record retrieval
        event = self.tracker.record_retrieval(retrievals, context)
        retrieval_result["retrieval_event_id"] = id(event)
        
        # Store event for later marking
        context["_retrieval_events"] = context.get("_retrieval_events", [])
        context["_retrieval_events"].append(event)
        
        return retrieval_result
    
    def mark_usage_after_reasoning(self, event_id: int, reasoning_output: str) -> None:
        """
        Mark retrieval usage after reasoning completes.
        
        Analyze reasoning_output to determine which retrievals were used.
        """
        # Simple heuristic: check if retrieval content appears in output
        output_lower = reasoning_output.lower()
        
        used = []
        for retrieval in self.tracker.retrieval_events[-1].get("retrieved", []):
            if retrieval.lower() in output_lower:
                used.append(retrieval)
        
        # Mark as used
        for event in self.tracker.retrieval_events:
            if id(event) == event_id:
                self.tracker.mark_used_in_output(id(event), used)
                break
    
    def get_current_rur(self) -> float:
        """Get current RUR metric."""
        return self.tracker.calculate_rur()
    
    def get_inflation_alert(self) -> Optional[str]:
        """Check for retrieval inflation."""
        inflation = self.tracker.get_retrieval_inflation_score()
        
        if inflation > 0.3:
            return f"🚨 RETRIEVAL INFLATION DETECTED: {inflation:.1%}"
        elif inflation > 0.1:
            return f"⚠️  Moderate retrieval inflation: {inflation:.1%}"
        
        return None

# ========= EXAMPLE USAGE =========
if __name__ == "__main__":
    # Example: Simulate retrieval flow
    instrumentation = RetrievalInstrumentation()
    
    # Simulate retrieval
    retrieval_result = {
        "context": {"query": "quantum computing", "pressure": "CRITICAL"},
        "retrievals": ["quantum_101", "quantum_102", "quantum_103"],
    }
    
    # Instrument retrieval
    retrieval_result = instrumentation.instrument_retrieval_flow(retrieval_result)
    print(f"Recorded retrieval event: {retrieval_result['retrieval_event_id']}")
    
    # Simulate reasoning that uses only 1 retrieval
    reasoning_output = "Quantum computing explores qubit superposition (quantum_101). Other sources not used."
    
    # Mark usage after reasoning
    instrumentation.mark_usage_after_reasoning(
        retrieval_result["retrieval_event_id"],
        reasoning_output
    )
    
    # Check RUR
    rur = instrumentation.get_current_rur()
    print(f"Current RUR: {rur:.2%}")
    
    # Check inflation alert
    alert = instrumentation.get_inflation_alert()
    if alert:
        print(alert)