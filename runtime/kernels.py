# RuntimeKernel - Central event coordinator

import asyncio
import sys
sys.path.insert(0, '/home/jason2ykk/.openclaw/workspace')

from runtime.memory import MemoryStore, MemoryGate
from runtime.sentinel import SentinelGovernor
from runtime.agent import RuntimeAgent
from runtime.bus import MessageBus
from datetime import datetime

class RuntimeKernel:
    """Central coordinator for event-driven architecture."""
    
    def __init__(self, agent_configs: list = None):
        """Initialize RuntimeKernel with agent configs."""
        self.agent_pool = []
        self.memory_store = MemoryStore()
        self.memory_gate = MemoryGate()
        self.sentinel = SentinelGovernor()
        self.message_bus = MessageBus()
        self.ddg = type('obj', (object,), {'search': lambda *args: None})
        self.tavily = type('obj', (object,), {'search': lambda *args: None})
        self.google = type('obj', (object,), {'search': lambda *args: None})
        
        # Agent initialization
        if agent_configs:
            self.initialize(agent_configs)
        
        # Pre-loaded agents (from memory)
        self.agent_configs = [
            {
                "id": "ops",
                "label": "ops",
                "model": "ollama/qwen3.5:9b",
                "tools": ["exec", "file_write", "file_fetch"]
            },
            {
                "id": "intel",
                "label": "intel",
                "model": "ollama/qwen3.5:9b",
                "tools": ["tavily_search", "tavily_extract", "web_search", "web_fetch"]
            }
        ]
        self.initialize(self.agent_configs)
    
    def initialize(self, agent_configs: list) -> None:
        """Initialize agent pool from configs."""
        for config in agent_configs:
            agent = RuntimeAgent(config['id'], config['model'])
            self.agent_pool.append(agent)
    
    def classify(self, query: str) -> str:
        """Classify query type for routing optimization."""
        query_lower = query.lower()
        if "latest" in query_lower or "2026" in query_lower:
            return "fresh"
        elif "how" in query_lower or "why" in query_lower:
            return "deep"
        return "general"
    
    async def handle(self, event: dict) -> any:
        """Main event handler - routes and executes."""
        try:
            # Step 1: Classify query for routing optimization
            qtype = self.classify(event.get("query", ""))
            print(f"Query Type: {qtype}")
            
            # Step 2: Route to appropriate agent
            agent = self.message_bus.route(event, qtype)
            
            # Step 3: Execute agent (isolated)
            result = await agent.run(event)
            
            # Step 4: Store response
            MemoryStore.write(agent.id, result)
            
            return result
        except Exception as e:
            self.logger.error(f"Kernel error: {e}")
            raise
    
    async def handle_web_search(self, event: dict) -> any:
        """Handle web_search events with parallel DDG→Tavily→Google chain."""
        query = event.get("query", "")
        qtype = self.classify(query)
        
        # OPTIMIZATION: Parallel execution
        ddg_task = asyncio.create_task(self.ddg.search(query, 5))
        tavily_task = asyncio.create_task(self.tavily.search(query, 3))
        google_task = asyncio.create_task(self.google.search(query, 3))
        
        try:
            ddg, tavily, google = await asyncio.gather(
                ddg_task, tavily_task, google_task
            )
            result = {"ddg": ddg, "tavily": tavily, "google": google}
        except Exception as e:
            result = {"error": str(e)}
        
        # STEP 7: Sentinel validation hook
        if not self.sentinel.validate(result):
            return {"status": "blocked"}
        
        return result
    
    def logger(self):
        """Return logger instance."""
        import logging
        return logging.getLogger("RuntimeKernel")
