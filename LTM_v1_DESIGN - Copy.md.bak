# Pentagon LTM v1 Architecture Design

## 📐 Architecture Diagram (Text Form)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      OPENCLAW LTM v1 LAYER                          │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │  Episodic   │  │ Semantic    │  │  Agent      │  │  Sentinel │ │
│  │   Memory    │  │   Memory    │  │   Memory    │  │   Layer   │ │
│  │  (Events)   │  │  (Facts)    │  │  (Per-Agt)  │  │ (Security)│ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │         │              │
│         ▼                ▼                ▼         ▼              │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                  MEMORY STORAGE LAYER                         │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │ │
│  │  │ LanceDB     │  │ Qdrant      │  │ Mem0        │          │ │
│  │  │ (Recent)    │  │ (Immutable) │  │ (Relation)  │          │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘          │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                            ▼                                       │
│                  ┌───────────────────────────────┐                │
│                  │      MEMORY OPERATIONS        │                │
│                  │  ┌──────────┐ ┌─────────────┐ │                │
│                  │  │ WRITE    │ │ RETRIEVE    │ │                │
│                  │  │          │ │             │ │                │
│                  │  └──────────┘ └─────────────┘ │                │
│                  │  ┌──────────┐ ┌─────────────┐ │                │
│                  │  │ SUMMARIZE│ │ VERIF (Sent)│ │                │
│                  │  │          │ │             │ │                │
│                  │  └──────────┘ └─────────────┘ │                │
│                  └───────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Data Schema (JSON)

### Point Schema (Qdrant Vector Store - Immutable Facts)
```json
{
  "point_id": "POINT_001",
  "collection": "pentagon_brain",
  "vector": [0.001, 0.002, ...],  // Embedding vector
  "payload": {
    "type": "semantic",
    "content": "RTX 4070 Super has 12GB VRAM",
    "source": "@ops",
    "timestamp": "2026-05-06T03:47:00+08",
    "tags": ["hardware", "specs"],
    "verified": true,
    "checksum": "sha256:abc123"
  }
}
```

### Vector Store Schema (LanceDB - Episodic Memory)
```json
{
  "sequence_id": "SEQ_20260506_001",
  "timestamp": "2026-05-06T03:49:00+08",
  "agents": ["main", "intel"],
  "events": [
    {
      "agent": "intel",
      "action": "web_search",
      "query": "latest AI trends",
      "status": "completed",
      "result_url": "https://example.com/article"
    },
    {
      "agent": "main",
      "action": "orchestrate",
      "task": "research synthesis",
      "status": "in_progress"
    }
  ],
  "summary": "Intel agent researching AI trends",
  "metadata": {
    "task_id": "TASK_001",
    "priority": "medium"
  }
}
```

### Agent Log Schema (Mem0 - Per-Agent)
```json
{
  "agent_id": "intel",
  "session_key": "session:main-intel-001",
  "actions": [
    {"type": "tavily_search", "query": "...", "timestamp": "..."},
    {"type": "file_fetch", "path": "...", "timestamp": "..."}
  ],
  "decisions": [
    {"reason": "...", "context": "..."}
  ],
  "errors": [],
  "tools_used": ["tavily_search", "web_fetch"]
}
```

## 🔄 Memory Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MEMORY WRITTING PIPELINE                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [1] Agent Action           → [2] Sentinel Verification             │
│       │                       │                                      │
│       ▼                       ▼                                      │
│  [3] Write to LanceDB       → [4] Vectorize & Index (Qdrant)       │
│       │                       │                                      │
│       ▼                       ▼                                      │
│  [5] Summary Generation     → [6] Store in Mem0 (Agent Logs)       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
         ▲                           ▲
         │                           │
┌────────┴─────────────────────────────────────────────────────────┐
│                     MEMORY RETRIEVAL PIPELINE                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [1] Query Received          → [2] Multi-Source Search            │
│       │                       │                                     │
│       ▼                       ▼                                     │
│  [3] Score & Rank            → [4] Summarize Results              │
│       │                       │                                     │
│       ▼                       ▼                                     │
│  [5] Return to Agent         → [6] Update Memory State            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## 🛡️ Sentinel Integration Points

### 1. Write Verification
- **Trigger:** Before memory write completes
- **Check:** Content validity, no PII leaks, checksum match
- **Action:** Reject if security violation detected

### 2. Read Authorization
- **Trigger:** Memory retrieval request
- **Check:** Agent permissions, data sensitivity level
- **Action:** Filter based on access control list

### 3. Hallucination Detection
- **Trigger:** Summary generation
- **Check:** Fact grounding in source material
- **Action:** Flag unverified claims for manual review

### 4. Memory Integrity
- **Trigger:** Periodic audits
- **Check:** Checksum validation, consistency checks
- **Action:** Quarantine corrupted entries

## 📊 Storage Strategy

| Memory Type | Store | TTL | Access Pattern |
|-------------|-------|-----|----------------|
| Episodic | LanceDB | 30 days | Recent-first (top-k) |
| Semantic | Qdrant | Permanent | Vector search, immutable |
| Agent | Mem0 | 7 days | Append-only, agent-specific |

## 🔧 Implementation Notes

### Lightweight Dependencies
- **No:** Python-heavy frameworks, heavy databases
- **Yes:** SQLite-compatible, pure Python where possible
- **Vector:** Use qdrant_client (thin wrapper)
- **Relation:** mem0ai (optimized for agent logs)

### VRAM Considerations
- Embedding model: quantized 8-bit
- Batch size: ≤4 for episodic writes
- Keep semantic cache in CPU RAM when possible

### Checksum Strategy
- SHA-256 for semantic facts (immutable)
- CRC32 for episodic summaries (speed)
- Verify on retrieval if modified

---
**Version:** 1.0.0  
**Architect:** Pentagon System @main  
**Status:** Ready for implementation  
**Review:** Pending @ops deployment validation