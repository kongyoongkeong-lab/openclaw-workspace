# TRUST BOUNDARY MAPPING
**Audit Phase:** STEP B-2 (Log Authority + WSL2 Boundaries)  
**Timestamp:** 2026-05-10 13:15+08:00

---

## 📦 A. LOG AUTHORITY CLASSIFICATION TABLE

| Source | Type | Definition | Authority Tier | Trust Level (0-1) | Verification Method |
|--------|------|------------|----------------|-------------------|---------------------|
| **kernel_stdout** | KERNEL | Direct WSL2 kernel output | L1 (Highest) | 0.95 | Syscall correlation |
| **kernel_stderr** | KERNEL | WSL2 kernel error events | L1 (Highest) | 0.90 | Syscall correlation |
| **openclaw_logs** | RUNTIME | Python/Ollama wrapper logs | L2 (High) | 0.70 | File I/O verification |
| **python_logs** | RUNTIME | Script output logs | L2 (High) | 0.65 | Hash comparison |
| **shell_outputs** | RUNTIME | Command stdout/stderr | L2 (High) | 0.75 | Path normalization |
| **llm_outputs** | MODEL | AI-generated responses | L0 (Lowest) | 0.30 | Semantic consistency |

### Authority Tier Definitions:
- **L1 (Kernel Truth):** Direct syscall-level evidence, unalterable
- **L2 (Runtime Evidence):** Wrapper logs, verifiable via file I/O
- **L0 (Inferred):** Model-generated or simulated outputs

### Trust Scoring Factors:
1. **Observability:** Was the event directly observed or inferred?
2. **Immutability:** Can the log be altered post-event?
3. **Attribution:** Can we trace to specific syscall?
4. **Context:** Available metadata (mounts, symlinks, permissions)

---

## 🧱 B. WSL2 MOUNT BOUNDARY DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│                 WINDOWS HOST (Windows 11 Pro)            │
│  /mnt/             /mnt/c → WSL2 mount to Windows C:    │
│  /mnt/d            /mnt/d → WSL2 mount to Windows D:    │
│                                                           │
│              ⚠️ TRUST LEAK POINT                          │
│              (Unrestricted access between layers)        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│               WSL2 KERNEL LAYER (Ubuntu 22.04)          │
│  /proc (pseudo-filesystem)                              │
│  /sys (kernel parameters)                                │
│                                                           │
│              🟢 KENREL ISOLATION BOUNDARY                │
│              (Unless explicitly breached)                 │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│           LINUX FILESYSTEM LAYER (OpenClaw Runtime)     │
│  /home/jason2ykk/.openclaw/workspace/                   │
│  /app/workspace/                                         │
│  /tmp/                                                    │
│                                                           │
│              🟡 SANDBOX BOUNDARY (Filesystem aliases)    │
│              (Symlink escape risk)                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│            OPENCLAW RUNTIME LAYER (Python Wrappers)    │
│  agent execution context                                 │
│  file I/O wrapper layer                                   │
│  process isolation                                         │
│                                                           │
│              🔴 RUNTIME ISOLATION (Process-level)        │
│              (Python subprocess leaks possible)           │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│              AGENT LAYER (Qwen/Gemini Models)           │
│  LLM prompts & responses                                  │
│  Tool invocation requests                                  │
│  Decision-making logic                                    │
│                                                           │
│              🟠 DECISION BOUNDARY (Logic-based)          │
│              (Hallucination risk)                          │
└─────────────────────────────────────────────────────────┘
```

### Critical Trust Boundaries:

| Boundary | Enforcement | Leak Risk | Detection Method |
|----------|-------------|-----------|------------------|
| **Host ↔ WSL2** | Mount table | High | `mount \| grep \` |
| **WSL2 Kernel** | Kernel hardening | Medium | `/proc/1/mountinfo` |
| **Filesystem Alias** | Symlink resolution | Critical | `readlink -f \` |
| **Runtime Sandbox** | Process isolation | Medium | `ps aux \| grep openclaw` |
| **Agent Logic** | Prompt injection | High | Content moderation |

---

## ⚠️ C. SYMLINK ESCAPE STRESS TEST (ANALYSIS)

### Test Vectors:

1. **Cross-Mount Traversal:**
   - `ln -s /mnt/c/Users/jason /home/jason2ykk/workspace/leak`
   - Access via `cat /home/jason2ykk/workspace/leak/file.txt`
   - **Expected:** WSL2 kernel follows symlink to host
   - **Risk:** FILESYSTEM LEAK

2. **Path Normalization Failure:**
   - `cd /tmp && ln -s / /tmp/escape && cd /tmp/escape/jason2ykk/.openclaw/workspace`
   - **Expected:** WSL2 allows absolute symlink resolution
   - **Risk:** PATH TRAVERSAL

3. **Bind Mount Leakage:**
   - Mount `/home` as readonly, then `ln -s /mnt/c /home/bridge`
   - **Expected:** WSL2 kernel allows bind mount bypass
   - **Risk:** MOUNT BOUNDARY BREACH

### Verification Commands:

```bash
# Check current mount points
mount | grep -E '/mnt|/home'

# Test symlink resolution
ln -sf /mnt/c /home/jason2ykk/workspace/test_link
readlink -f /home/jason2ykk/workspace/test_link

# Verify WSL2 isolation
cat /proc/1/mountinfo
```

---

## 📊 SUMMARY OF CURRENT TRUTH GAPS

| Gap | Impact | Resolution Priority |
|-----|--------|--------------------|
| **Log authority unknown** | Cannot distinguish real vs simulated | CRITICAL |
| **Symlink escape untested** | Filesystem boundary leak | HIGH |
| **Mount table unverified** | Unknown WSL2 isolation | HIGH |
| **Attribution integrity** | Cannot trace syscall → agent | MEDIUM |

---

## 🧭 NEXT STEPS (STEP B-3)

1. **Run mount boundary verification** - Confirm `/mnt/c` isolation
2. **Execute symlink escape test** - Proven or refute the risk
3. **Build execution truth table** - Map each operation to trust tier
4. **Prepare verdict engine inputs** - Only after gaps filled

**Status:** STEP B-2 INCOMPLETE (waiting for gap fill before proceeding)

---

*Audit Status: 🔴 WAITING FOR TRUTH VERIFICATION*
