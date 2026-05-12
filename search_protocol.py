#!/usr/bin/env python3
"""
search_protocol.py - Web Search Protocol with SPG Integration

Chain: DDG (Discover) → Tavily (Extract) → Google (Verify)

SPG Pressure Gates:
- SAFE/EARLY: Full chain execution
- THROTTLE: Use only Tavily (skip Google verify)
- CRITICAL: Use Tavily only, limit results
- EMERGENCY: Deny searches

Architecture:
1. DDG: Discover relevant topics
2. Tavily: Extract clean content
3. Google: Verify accuracy
4. Synthesis: Consolidate results
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests

from spg import get_sp_governor

# API Constants
TAVILY_API_KEY = ""  # Set in environment
DDG_API_URL = "https://lite.duckduckgo.com/lite"
TAVILY_SEARCH_URL = "https://api.tavily.com/search"

class SearchProtocol:
    """
    Web search chain with SPG pressure integration.
    
    Flow:
    1. DDG Discover (free, fast)
    2. Tavily Extract (clean, structured)
    3. Google Verify (accuracy check)
    4. Synthesis (consolidate)
    """
    
    def __init__(self, workspace: str):
        self.workspace = Path(workspace)
        self.spg = get_sp_governor()
        self._tavily_available = Tavily.is_available()
        self._tavily_api_key = Tavily.get_api_key()
    
    def get_pressure_signal(self) -> str:
        """Get current SPG pressure signal."""
        return self.spg.get_pressure_signal()
    
    def get_pressure_zone(self) -> str:
        """Get current SPG pressure zone."""
        pressure_data = self.spg.calculate_pressure()
        return pressure_data["zone"]
    
    def is_pressure_allowed(self) -> bool:
        """Check if search is allowed under current pressure."""
        zone = self.get_pressure_zone()
        return zone != "EMERGENCY"
    
    def execute_ddg_discovery(self, query: str) -> Dict[str, Any]:
        """Step 1: DDG Discover."""
        try:
            # DDG Lite search
            headers = {"Accept": "application/json"}
            params = {
                "q": query,
                "kl": "en_US",
                "ff": "true",
            }
            response = requests.get(DDG_API_URL, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return {
                    "step": "ddg_discover",
                    "status": "success",
                    "response": response.json(),
                }
            else:
                return {
                    "step": "ddg_discover",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "step": "ddg_discover",
                "status": "exception",
                "error": str(e),
            }
    
    def execute_tavily_extraction(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Step 2: Tavily Extract (primary source)."""
        if not self._tavily_available or not self._tavily_api_key:
            return {
                "step": "tavily_extract",
                "status": "denied_api",
                "reason": "Tavily API key not configured or unavailable",
            }
        
        try:
            response = requests.post(
                TAVILY_SEARCH_URL,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                    "include_images": False,
                },
                timeout=15
            )
            
            if response.status_code == 200:
                return {
                    "step": "tavily_extract",
                    "status": "success",
                    "results": response.json().get("results", []),
                    "answer": response.json().get("answer", ""),
                }
            else:
                return {
                    "step": "tavily_extract",
                    "status": "failed",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            return {
                "step": "tavily_extract",
                "status": "exception",
                "error": str(e),
            }
    
    def execute_google_verification(self, query: str, results: List[Dict]) -> Dict[str, Any]:
        """Step 3: Google Verify (accuracy check)."""
        try:
            # Note: Google search API requires API key
            # For now, use web_search as fallback
            from web_search import GoogleSearch
            
            search = GoogleSearch()
            verified_results = search.search(query, count=3)
            
            return {
                "step": "google_verify",
                "status": "success",
                "verified_sources": len(verified_results.get("organic", [])),
                "verified_results": verified_results.get("organic", []),
            }
        except Exception as e:
            return {
                "step": "google_verify",
                "status": "exception",
                "error": str(e),
            }
    
    def synthesize_results(self, ddg_result: Dict, tavily_result: Dict, 
                          google_result: Dict) -> Dict[str, Any]:
        """Step 4: Synthesize consolidated results."""
        all_results = []
        
        # Collect results from each step
        if tavily_result.get("status") == "success":
            all_results.extend(tavily_result.get("results", []))
        
        if google_result.get("status") == "success":
            all_results.extend(google_result.get("verified_results", []))
        
        # Remove duplicates
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return {
            "step": "synthesis",
            "status": "success",
            "total_sources": len(unique_results),
            "final_results": unique_results[:5],  # Top 5
        }
    
    def execute_full_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Execute full search chain with SPG pressure gating."""
        signal = self.get_pressure_signal()
        zone = self.get_pressure_zone()
        
        # Pressure gate
        if zone == "EMERGENCY":
            return {
                "status": "denied",
                "zone": zone,
                "signal": signal,
                "reason": "EMERGENCY: deny search requests",
            }
        
        elif zone == "CRITICAL":
            # Only Tavily, limit results
            tavily_result = self.execute_tavily_extraction(query, max_results=2)
            return {
                "status": "partial_search",
                "zone": zone,
                "signal": signal,
                "reason": "CRITICAL: Tavily only, limited results",
                "results": tavily_result.get("results", [])[:2],
            }
        
        elif zone == "THROTTLE":
            # Tavily only, skip Google
            tavily_result = self.execute_tavily_extraction(query, max_results=3)
            return {
                "status": "throttled_search",
                "zone": zone,
                "signal": signal,
                "reason": "THROTTLE: Tavily only, no Google verify",
                "results": tavily_result.get("results", [])[:3],
            }
        
        else:
            # Full chain: DDG → Tavily → Google
            # Step 1: DDG Discover
            ddg_result = self.execute_ddg_discovery(query)
            
            # Step 2: Tavily Extract
            tavily_result = self.execute_tavily_extraction(query, max_results)
            
            # Step 3: Google Verify
            google_result = self.execute_google_verification(query, tavily_result.get("results", []))
            
            # Step 4: Synthesis
            synthesized = self.synthesize_results(ddg_result, tavily_result, google_result)
            
            return {
                "status": "full_search",
                "zone": zone,
                "signal": signal,
                "results": synthesized.get("final_results", []),
                "total_sources": synthesized.get("total_sources", 0),
            }
    
    def quick_search(self, query: str) -> Dict[str, Any]:
        """Quick search using only Tavily (faster)."""
        if not self.is_pressure_allowed():
            return {"status": "denied", "reason": "Pressure too high"}
        
        return self.execute_tavily_extraction(query)
    
    def get_recommendation(self) -> str:
        """Get SPG recommendation."""
        return self.spg.get_recommendation()


class SearchIntegration:
    """Integration layer for Pentagon agents."""
    
    def __init__(self, workspace: str):
        self.protocol = SearchProtocol(workspace)
        self.workspace = Path(workspace)
    
    def search(self, query: str, agent: str = "intel") -> Dict[str, Any]:
        """Search with agent-specific handling."""
        if agent == "intel":
            result = self.protocol.execute_full_search(query)
        else:
            result = self.protocol.quick_search(query)
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """Check search health."""
        return {
            "tavily_available": self.protocol._tavily_available,
            "tavily_key": "configured" if self.protocol._tavily_api_key else "not configured",
            "signal": self.protocol.get_pressure_signal(),
        }


# Tavily wrapper
class Tavily:
    @staticmethod
    def is_available() -> bool:
        """Check if Tavily is available."""
        # Check API key
        return bool(Tavily.get_api_key())
    
    @staticmethod
    def get_api_key() -> str:
        """Get Tavily API key from environment."""
        import os
        return os.environ.get("TAVILY_API_KEY", "")
    
    @staticmethod
    def search(query: str, max_results: int = 5) -> Dict[str, Any]:
        """Tavily search wrapper."""
        if not Tavily.is_available():
            return {"status": "error", "reason": "API key not configured"}
        
        response = requests.post(
            TAVILY_SEARCH_URL,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            json={
                "query": query,
                "max_results": max_results,
                "include_answer": False,
            },
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "error", "error": response.text}


def init_pressure_aware_search(workspace: Optional[str] = None) -> SearchIntegration:
    """Initialize pressure-aware search."""
    return SearchIntegration(workspace=workspace)


if __name__ == "__main__":
    search = init_pressure_aware_search("/home/jason2ykk/.openclaw/workspace")
    signal = search.protocol.get_pressure_signal()
    
    print("🔍 Pentagon Search Protocol Initialized")
    print(f"Initial Signal: {signal}")
    print("\nCommands: search, quick, health, quit\n")
    
    while True:
        try:
            cmd = input("Enter command: ")
            
            if cmd.strip().lower() in ["quit", "exit", "q"]:
                break
            
            elif cmd.strip().lower() == "health":
                print(json.dumps(search.health_check(), indent=2))
            
            else:
                result = search.search(cmd.strip())
                print(json.dumps(result, indent=2))
                
        except EOFError:
            break
