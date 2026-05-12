# 🔴 Phase 2: Controlled Contention Test

**Goal:** Stress orchestration, not load.

## 🔴 Stage 1: Shared Resource Contention

**Inject:**
- @intel: 3 concurrent web crawls (same rate limit)
- @ops: 2 concurrent Python jobs (same temp workspace)
- @comms: Aggregates logs from both (contention points)
- **Shared lock:** `/home/jason2ykk/.openclaw/workspace/test_contention/`

**Goal:** Force arbitration decisions

## 🔴 Stage 2: Controlled Failure Injection

**Trigger:** Simulated workspace permission violation (safe mock)

**Goal:** Verify repair action execution (not just observation)

## 🔴 Stage 3: Conflict Resolution Verification

**Check:**
- Only ONE repair action executed?
- Cooldowns blocked duplicate responses?
- Lower priority actions queued correctly?

**⏱️ Timeline:**
- Total: 20-30 min
- Contention window: 15 min
- Failure injection: t+5 min
- Verification: t+20 min
