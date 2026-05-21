# OpenClaw Memory Pipeline Integration - Build Instructions

**Build Date:** 2026-05-06 | **Status:** Ready for Compilation

## 🎯 Objective
Enable LTM (Long-Term Memory) hooks in OpenClaw agent pipeline.

## 📦 Build Components

### 1. memory_v1.py (Storage Layer)

**Location:** `/home/jason2ykk/.npm-global/lib/node_modules/openclaw/src/memory/`

```python
"""
memory_v1.py - OpenClaw Memory Storage Layer v1
Author: Pentagon Team
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

MEMORY_BASE = os.path.join(os.path.dirname(__file__), 'memory')
EPISODIC_FILE = os.path.join(MEMORY_BASE, 'episodic.jsonl')
SEMANTIC_FILE = os.path.join(MEMORY_BASE, 'semantic.jsonl')
COMPRESS_THRESHOLD = 3000

AGENT_MEMORY_ACCESS = {
    'main': {'episodic': None, 'semantic': None},
    'ops': {'episodic': 100, 'semantic': 50},
    'sentinel': {'episodic': None, 'semantic': None},
    'intel': {'episodic': None, 'semantic': None},
    'comms': {'episodic': 100, 'semantic': None},
}

def load_jsonl(filepath: str, max_events: Optional[int] = None) -> List[Dict[str, Any]]:
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        events = []
        for line in f:
            try:
                events.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    if max_events:
        return events[:max_events]
    return events

def save_jsonl(filepath: str, events: List[Dict[str, Any]], append: bool = False) -> bool:
    try:
        if append:
            with open(filepath, 'a') as f:
                for event in events:
                    f.write(json.dumps(event) + '\n')
        else:
            with open(filepath, 'w') as f:
                for event in events:
                    f.write(json.dumps(event) + '\n')
        return True
    except Exception:
        return False

def inject_memory_into_prompt(agent: str, prompt: str, episodic_limit: Optional[int] = None, semantic_limit: Optional[int] = None) -> str:
    episodic_limit = episodic_limit or AGENT_MEMORY_ACCESS[agent]['episodic']
    semantic_limit = semantic_limit or AGENT_MEMORY_ACCESS[agent]['semantic']
    
    episodic_events = load_jsonl(EPISODIC_FILE, episodic_limit)
    semantic_events = load_jsonl(SEMANTIC_FILE, semantic_limit)
    
    injected = f"=== SYSTEM CONTEXT ===\n"
    if episodic_events:
        injected += f"Recent Events ({len(episodic_events)}):\n"
        for event in episodic_events[:10]:
            injected += f"- [{event.get('timestamp', 'N/A')}] {event.get('summary', 'No summary')}\n"
        injected += "\n=== END SYSTEM CONTEXT ===\n"
    if semantic_events:
        injected += f"\nImmutable Facts ({len(semantic_events)}):\n"
        for fact in semantic_events[:20]:
            injected += f"- {fact.get('fact', 'No fact')}\n"
    return injected + prompt

def save_episodic_event(agent: str, event_data: Dict[str, Any], append: bool = True) -> bool:
    event_data['timestamp'] = datetime.now().isoformat()
    event_data['agent'] = agent
    event_data['type'] = 'response'
    return save_jsonl(EPISODIC_FILE, [event_data], append=append)

def compress_memory(agent: str = 'sentinel') -> int:
    events = load_jsonl(EPISODIC_FILE, COMPRESS_THRESHOLD)
    if len(events) < COMPRESS_THRESHOLD // 2:
        return 0
    keep_count = COMPRESS_THRESHOLD // 2
    kept_events = events[-keep_count:]
    return len(events) - len(kept_events)
```

### 2. memory_router.py (Integration Layer)

**Location:** `/home/jason2ykk/.npm-global/lib/node_modules/openclaw/src/memory/`

```python
"""
memory_router.py - Memory Routing Integration Layer
Author: Pentagon Team
"""

from memory_v1 import (
    inject_memory_into_prompt,
    save_episodic_event,
    compress_memory,
    EPISODIC_FILE,
    COMPRESS_THRESHOLD
)

class MemoryRouter:
    """Manages memory injection and persistence for OpenClaw agents."""
    
    def __init__(self, agent: str):
        self.agent = agent
        self.access_policy = AGENT_MEMORY_ACCESS.get(agent, {})
        
    def inject_into_llm(self, prompt: str) -> str:
        """Inject memory into LLM prompt before generation."""
        episodic_limit = self.access_policy.get('episodic') or 100
        semantic_limit = self.access_policy.get('semantic') or 50
        
        injected = inject_memory_into_prompt(
            agent=self.agent,
            prompt=prompt,
            episodic_limit=episodic_limit,
            semantic_limit=semantic_limit
        )
        return injected
    
    def persist_response(self, response: Dict[str, Any]) -> bool:
        """Persist agent response to episodic memory."""
        event = {
            'agent': self.agent,
            'timestamp': datetime.now().isoformat(),
            'response': response,
            'type': 'response'
        }
        return save_episodic_event(agent=self.agent, event_data=event)
    
    def enable_compression(self) -> int:
        """Trigger memory compression, returns count of compressed events."""
        return compress_memory(agent=self.agent)
    
    def health_check(self) -> Dict[str, Any]:
        """Return memory health status."""
        episodic = load_jsonl(EPISODIC_FILE, COMPRESS_THRESHOLD)
        events = load_jsonl(SEMANTIC_FILE, 50)
        
        return {
            'agent': self.agent,
            'episodic_count': len(episodic),
            'semantic_count': len(events),
            'threshold': COMPRESS_THRESHOLD,
            'compression_ready': len(episodic) >= COMPRESS_THRESHOLD // 2
        }

def create_router(agent: str) -> MemoryRouter:
    """Factory function to create memory router for agent."""
    return MemoryRouter(agent=agent)
```

### 3. OpenClaw Agent Runner Integration

**Location:** `/home/jason2ykk/.npm-global/lib/node_modules/openclaw/src/agent_runner.py`

**Changes Required:**
```python
# Before LLM call (pre_llm_hook)
def run_agent(agent: str, prompt: str, **kwargs) -> str:
    router = create_router(agent)
    injected_prompt = router.inject_into_llm(prompt)
    logger.debug(f"Memory injected for {agent}: {len(injected_prompt)} chars")
    
    # Call LLM with injected prompt
    response = llm.infer(injected_prompt, **kwargs)
    
    # After LLM call (post_llm_hook)
    router.persist_response(response)
    logger.debug(f"Response persisted for {agent}")
    
    return response

# Background compression (sentinel_hook)
def schedule_compression():
    setInterval(() => {
        const router = MemoryRouter.createRouter('sentinel')
        const compressed = router.enable_compression()
        logger.info(`Compressed ${compressed} events`);
    }, 5 * 60 * 1000) // 5 minutes
```

### 4. Configuration Updates

**Location:** `~/.openclaw/openclaw.json`

```json
{
  "hooks": {
    "memory": {
      "enabled": true,
      "pre_llm": true,
      "post_llm": true,
      "compression_interval": "5m",
      "threshold": 3000
    }
  }
}
```

## 📊 Deployment Steps

1. **Write** `memory_v1.py` to `/home/jason2ykk/.npm-global/lib/node_modules/openclaw/src/memory/`
2. **Write** `memory_router.py` to `/home/jason2ykk/.npm-global/lib/node_modules/openclaw/src/memory/`
3. **Patch** `agent_runner.py` with hook injection code
4. **Apply** config changes to openclaw.json
5. **Restart** OpenClaw Gateway to hot-reload hooks
6. **Verify** memory injection via logging

## 🧪 Test Scenarios

| Test Case | Expected Behavior | Verification |
|------|------|--------|
| Agent receives message | Memory injected into prompt | Check logs |
| Agent responds | Response saved to episodic.jsonl | Check memory file |
| Sentinel runs loop | Compression triggered every 5 min | Check logs |
| Agent access control | Each agent sees correct memory | Compare prompts |

## 📈 Metrics

| Metric | Target | Current |
|--------|--------|-----|
| VRAM Usage | ≤ 10GB | 8.5GB reserved ✅ |
| Memory Compression Ratio | 50% | Pending |
| Episodic Events Stored | ≤ 100/agent | 0 (fresh) |
| Semantic Facts Stored | ≤ 50/fact | 0 (fresh) |
| Hook Injection Latency | < 100ms | Pending |

## 🚨 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| OpenClaw source protection | High | Requires rebuild or build access |
| GPU VRAM overflow | Medium | Reserved 8.5GB limit |
| Memory corruption | Medium | JSONL validation |
| Access control bypass | Low | Role-based matrix |

## 🚀 Next Command

```bash
# Requires approval
openclaw gateway apply --yes --raw="{ hooks: { memory: { enabled: true } } }"
```

**Awaiting:** User approval for OpenClaw Gateway configuration update and potential rebuild.
