# 🔍 SEARCH POLICY V1.0
# Single Source of Governance Truth
# Status: Active (Strict Mode)

---

## 📊 SEARCH STATES

| State | Meaning | Allowed Tools |
| ---------- | ------ | -------------- |
| **PASSIVE** | No web retrieval | none |
| **LIGHT** | Lightweight queries | web_search (basic) |
| **RESEARCH** | Technical synthesis | tavily_search (advanced) |
| **GOVERNANCE** | High-confidence guidance | tavily_search + extract + validate |
| **LOCKDOWN** | External retrieval suppressed | offline only |

---

## 📦 EXECUTION TIERS

### Tier S1 — Lightweight Retrieval
- **Purpose:** Minimal cognition cost
- **Allowed:** web_search, web_fetch
- **Constraints:**
  - Token budget: ≤2K
  - Top-K: 1-3
  - No memory injection
  - Low authority

### Tier S2 — Intelligence Retrieval
- **Purpose:** Semantic understanding
- **Allowed:** tavily_search (basic)
- **Constraints:**
  - Token budget: ≤6K
  - Top-K: 5
  - Summarization required
  - Bounded execution

### Tier S3 — Governance Validation
- **Purpose:** High-confidence operational guidance
- **Required:**
  - Tavily advanced search
  - Official source confirmation
  - Structured extraction
  - Confidence scoring
- **Tools:** tavily_search, tavily_extract, web_fetch

### Tier S4 — Critical Arbitration
- **Purpose:** Safe infrastructure decision support
- **Required:**
  - Multi-source consensus
  - Telemetry alignment
  - Governance approval
  - Quarantine memory
- **Status:** No autonomous execution

---

## 🛡️ AUTHORITY LEVELS

| Level | Trust | Use Case |
| ------ | ------ | --------- |
| **L1 Trusted** | Internal docs, known sources | Routine queries |
| **L2 Verified** | External + official sources | Technical troubleshooting |
| **L3 Confirmed** | Multi-source consensus | Governance validation |
| **L4 Quarantined** | External high-risk | Audit review only |

---

## 📏 BUDGET PARAMETERS

### Token Budgets
| Tier | Budget |
| ------ | ------ |
| S1 | ≤2K |
| S2 | ≤6K |
| S3 | ≤10K |
| S4 | ≤15K + quarantine |

### Latency Budgets
| Tier | Budget |
| ------ | ------ |
| S1 | ≤3s |
| S2 | ≤8s |
| S3 | ≤15s |
| S4 | ≤30s + approval |

### Retrieval Budget
| Tier | Top-K |
| ------ | ------ |
| S1 | 1-3 |
| S2 | 5 |
| S3 | 10 |
| S4 | 15 + cross-ref |

---

## 🧭 TOOL ROUTING RULES

| Query Type | Preferred Tool | Depth |
| ------ | --------- | ------ |
| Technical debugging | tavily_search | advanced |
| Quick URL fetch | web_fetch | - |
| Broad web lookup | web_search | basic |
| Structured extraction | tavily_extract | - |
| Governance repair | tavily_search + extract | advanced |
| News | tavily_search topic=news | basic |
| Finance | tavily_search topic=finance | advanced |
| Dependency validation | web_fetch | - |
| Architecture research | tavily_search | advanced |

---

## 🚫 RECURSION LIMITS

| Metric | Limit |
| ------ | ------ |
| Max depth | 3 (unless S4 approval) |
| Loop detection | 3 identical queries |
| Amplification factor | ≤2.0 |
| Stop condition | Authority < L2 |

---

## 🧪 QUARANTINE RULES

External memory safety:

1. **All external results enter quarantine**
2. **No quarantine content enters governance reasoning directly**
3. **Summarization required before promotion**
4. **Authority score < L2 = rejection**
5. **Quarantine retention: 7 days max**

---

## 📝 SUMMARIZATION REQUIREMENTS

Every Tavily advanced result MUST pass:

```
raw retrieval → sanitization → deduplication → compression → governance digest
```

NOT: raw retrieval → agent

---

## ⚡ ESCALATION RULES

Governance gating:

| Condition | Action |
| ---------- | ------ |
| Authority < L2 | Reject or request validation |
| Retrieval noise > 0.3 | Trigger compression |
| Recursion limit hit | Abort + alert |
| Token budget exceeded | Downgrade tier or reject |
| Authority conflict | Escalate to S4 review |

---

## 📈 SEARCH METRICS (HEARTBEAT)

### Essential (v1)
- search_latency_p95
- search_budget_usage
- authority_confidence
- retrieval_noise_ratio
- search_failure_rate
- search_amplification_factor

### Advanced (v2)
- semantic_divergence
- retrieval_entropy
- authority_decay
- confidence_half-life

---

## 🚨 SAFETY RULES

1. **No raw web content enters governance reasoning directly**
2. **All web content must pass: sanitization, compression, authority scoring, relevance filtering**
3. **Search costs must be accounted per query**
4. **External retrieval suppressed in LOCKDOWN state**
5. **No autonomous S4 execution**

---

## 🔧 CONFIGURATION

### Policy Enforcement
- **Mode:** Strict
- **Bypass:** Governance approval only
- **Overrides:** Logged + audited

### Cost Accounting
Every query carries:
- token_cost
- latency_cost
- authority_risk
- recursion_risk

---

## 📅 VERSIONING

- **Version:** 1.0
- **Effective:** 2026-05-13
- **Author:** @main (Pentagon System Orchestrator)
- **Review:** H1 checkpoint (24h)

---

**End of Policy Document**
**Status: Active | Strict Mode**
