# 🏗 Agent Context Isolation Architecture

## 🎯 Objective
Replace shared global memory (`memory.jsonl`) with **localized agent memory stores** to prevent context bleeding and enable scalable multi-agent systems.

---

## 🔄 Topology Migration

### BEFORE: Shared-Context Topology
```
┌─────────────────────────────────────────────┐
│           memory.jsonl (Single Source)      │
│  ┌────────┬────────┬────────┬────────┐     │
│  │ User   │ @intel │ @ops   │ @comms │     │
│  │ Input  │ Search │ Exec   │ Output  │     │
│  └────────┴────────┴────────┴────────┘     │
└─────────────────────────────────────────────┘
                ▲
        Retrieval-based filtering
```

**Issues:**
1. Context bleeding: @intel search results pollute @ops
2. No agent-specific memory persistence
3. Token budgeting is secondary, not primary guardrail
4. Single point of contention (memory.jsonl)

---

### AFTER: Localized Memory Topology
```
┌──────────────────────────────────────────────────────┐
│                 Agent Memory Stores                    │
│                                                       │
│  @main ─────────┐  ┌────────────────────────────┐   │
│  ┌─────────────┐ │ │        Shared Semantic      │   │
│  │ Episodic    │ │ │          Vault (Qdrant)    │   │
│  │ memory.jsonl │ │ │    Immutable Facts         │   │
│  └─────────────┘ │ └────────────────────────────┘   │
│                  │                                   │
│  @intel ─────────┼──────────────────────────────────┤
│  ┌─────────────┐ │                                   │
│  │ Episodic    │ │                                   │
│  │ search.jsonl│ │                                   │
│  └─────────────┘ │                                   │
│                  │                                   │
│  @ops ───────────┼──────────────────────────────────┤
│  ┌─────────────┐ │                                   │
│  │ Episodic    │ │                                   │
│  │ exec.jsonl  │ │                                   │
│  └─────────────┘ │                                   │
│                  │                                   │
│  @comms ─────────┼──────────────────────────────────┤
│  ┌─────────────┐ │                                   │
│  │ Episodic    │ │                                   │
│  │ comms.jsonl │ │                                   │
│  └─────────────┘ │                                   │
│                  │                                   │
│  @sentinel ───────┴──────────────────────────────────┤
│  ┌─────────────┐                                      │
│  │ Episodic    │                                      │
│  │ sentinel.jsonl│                                   │
│  └─────────────┘                                      │
└──────────────────────────────────────────────────────┘
```

---

## 📦 Data Structure

### Per-Agent Memory Store Format
```json
{
  "agent": "@intel",
  "type": "episodic",
  "ts": 1715223600,
  "datetime": "2026-05-08T22:00:00Z",
  "content": "Searched tavily for 'LLM optimization'",
  "meta": {
    "tokens": 1500,
    "source": "tavily_search",
    "query": "LLM optimization"
  }
}
```

### Shared Semantic Vault (Immutable)
```json
{
  "id": 123,
  "vector": [...],
  "payload": {
    "agent": "any",
    "fact": "qwen3.5:9b deployed on RTX 4070 Super",
    "immutable": true
  }
}
```

---

## 🛠 Implementation Strategy

### Phase 1: Create Agent-Specific Memory Files
- `memory/intel/search.jsonl`
- `memory/ops/exec.jsonl`
- `memory/comms/output.jsonl`
- `memory/sentinel/audit.jsonl`

### Phase 2: Build Memory Router
- Route each agent's writes to their专属 store
- Shared vault for immutable facts (Qdrant)

### Phase 3: Update Pipeline
- Modify `ltm_pipeline.py` to accept `agent` parameter
- Each agent writes to its store
- Retrieval queries agent-specific store + shared vault

### Phase 4: Cross-Agent Context Sharing (Controlled)
- @main compressed summaries → shared read-only
- Shared semantic vault (Qdrant) for immutable facts
- No direct cross-write allowed

---

## 🔄 Migration Path

### Step 1: Backward Compatibility Layer
```python
# Legacy: memory.jsonl (read-only for reference)
# New: Agent-specific stores (active)
```

### Step 2: Gradual Migration
- Keep `memory.jsonl` append-only (legacy compatibility)
- New events go to agent-specific stores
- Deprecate `memory.jsonl` reads after 30 days

### Step 3: Full Migration
- Stop writes to `memory.jsonl`
- Migrate legacy data to semantic vault
- Deprecate `memory.jsonl` entirely

---

## 🎯 Benefits

1. **Isolation:** Agents cannot pollute each other's context
2. **Scalability:** Easy to add new agents without memory contention
3. **Debugging:** Per-agent logs for issue tracing
4. **Security:** @sentinel can audit only its store
5. **Token Efficiency:** Each agent only sees relevant context

---

## ⚠️ Critical Rules

1. **No Cross-Writes:** @intel cannot write to @ops memory
2. **@main as Aggregator:** Only @main can read all agent stores for summaries
3. **Vault Immutability:** Semantic vault entries never overwritten
4. **Token Budgeting:** Apply per-agent, not globally

---

## 📝 Status

- [x] Architecture designed
- [ ] Memory router implementation
- [ ] Agent-specific store creation
- [ ] Pipeline refactoring
- [ ] Migration testing
- [ ] Production deployment
