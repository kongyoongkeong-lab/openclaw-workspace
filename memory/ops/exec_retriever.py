#!/usr/bin/env python3
"""
ops/exec_retriever.py — Agent-Specific Memory Retriever

@ops 专属检索层：只检索自己的执行历史
禁止访问其他 agents 的记忆
"""

import sys
sys.path.insert(0, "/home/jason2ykk/.openclaw/workspace/memory")

from memory_router import read_agent_memory, read_shared_vault


class OpsRetriever:
    """@ops 专属检索器"""
    
    def __init__(self, agent: str = "ops"):
        self.agent = agent
        self.store_path = f"/home/jason2ykk/.openclaw/workspace/memory/{agent}/exec.jsonl"
    
    def retrieve_execution_state(self, query: str, top_k: int = 3) -> list:
        """
        @ops 专属检索：自己的执行状态
        """
        return read_agent_memory(self.agent, top_k)
    
    def retrieve_shared_facts(self, query: str, top_k: int = 2) -> list:
        """
        从共享语义 vault 检索少量事实
        @ops 只能访问很少的共享事实
        """
        return read_shared_vault(query, top_k)
    
    def retrieve(self, query: str, query_type: str = "execution", top_k: int = 5) -> list:
        """
        @ops 专属检索预算：
        - execution state: k=3 (自己的执行)
        - semantic facts: k=2 (共享 vault，极少量)
        - TOTAL: k=5 (strict budget)
        """
        if query_type == "execution":
            exec_results = self.retrieve_execution_state(query, top_k=3)
        else:
            exec_results = []
        
        if query_type in ["semantic", "mixed"]:
            facts = self.retrieve_shared_facts(query, top_k=2)
        else:
            facts = []
        
        return exec_results + facts
    
    def is_outside_scope(self, event: dict) -> bool:
        """
        检查事件是否超出 @ops 检索范围
        """
        agent = event.get("agent", "")
        # @ops 只能检索自己的执行历史或极少共享 vault
        if agent not in [self.agent, "vault"]:
            return True
        return False


if __name__ == "__main__":
    retriever = OpsRetriever()
    
    print("=== @ops 专属检索器测试 ===")
    
    # Test
    results = retriever.retrieve("Docker deployment", query_type="execution")
    print(f"\n检索结果 for 'Docker deployment':")
    for r in results:
        print(f"  Agent: {r.get('agent')}, Content: {r['content'][:60]}...")
