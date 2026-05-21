#!/usr/bin/env python3
"""
intel/search_retriever.py — Agent-Specific Memory Retriever

@intel专属检索层：只检索自己的搜索历史 + 共享语义 vault
禁止访问其他 agents 的记忆
"""

import sys
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_router import read_agent_memory, read_shared_vault


class IntelRetriever:
    """@intel 专属检索器"""
    
    def __init__(self, agent: str = "intel"):
        self.agent = agent
        self.store_path = f"/home/jason2ykk/.openclaw/workspace/memory/{agent}/search.jsonl"
    
    def retrieve_search_history(self, query: str, top_k: int = 3) -> list:
        """
        @intel 专属检索：自己的搜索历史
        """
        return read_agent_memory(self.agent, top_k)
    
    def retrieve_shared_facts(self, query: str, top_k: int = 5) -> list:
        """
        从共享语义 vault 检索事实
        """
        return read_shared_vault(query, top_k)
    
    def retrieve(self, query: str, query_type: str = "search", top_k: int = 5) -> list:
        """
        @intel 专属检索预算：
        - search history: k=3 (自己的搜索)
        - semantic facts: k=5 (共享 vault)
        - TOTAL: k=8 (strict budget)
        """
        if query_type == "search":
            search_results = self.retrieve_search_history(query, top_k=3)
        else:
            search_results = []
        
        if query_type in ["semantic", "mixed"]:
            facts = self.retrieve_shared_facts(query, top_k=5)
        else:
            facts = []
        
        return search_results + facts
    
    def is_outside_scope(self, event: dict) -> bool:
        """
        检查事件是否超出 @intel 检索范围
        """
        agent = event.get("agent", "")
        # @intel 只能检索自己的搜索历史或共享 vault
        if agent not in [self.agent, "vault", "shared"]:
            return True
        return False


if __name__ == "__main__":
    retriever = IntelRetriever()
    
    print("=== @intel 专属检索器测试 ===")
    
    # Test
    results = retriever.retrieve("Python deployment", query_type="mixed")
    print(f"\n检索结果 for 'Python deployment':")
    for r in results:
        print(f"  Agent: {r.get('agent')}, Content: {r['content'][:60]}...")
