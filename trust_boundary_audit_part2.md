# 📊 STEP B-2: TRUST BOUNDARY MAPPING
**Timestamp:** 2026-05-10 12:43+08:00  
**Status:** PART 1/2 COMPLETE

---

## A. LOG AUTHORITY TABLE

| Source | Authority Tier | Trust Level | Verification Method |
|--------|----------------|-------------|---------------------|
| **kernel** (dmesg) | L0 - Kernel Syscall | ✅ AUTHENTIC | Direct hardware interrupt / syscall trace |
| **/proc/1/cmdline** | L0 - Kernel Init | ✅ AUTHENTIC | PID 1 init process (kernel-trusted) |
| **systemd-journald** | L1 - Runtime Wrapper | ⚠️ SEMI-TRUSTED | Syslog daemon (may filter/aggregate) |
| **journalctl** | L1 - Runtime Wrapper | ⚠️ SEMI-TRUSTED | Same as above |
| **openclaw logs** | L1.5 - Agent Wrapper | ⚠️ LOW-TRUST | Python wrapper (may omit/syslog) |
| **python logs** | L1.5 - Runtime Wrapper | ⚠️ LOW-TRUST | Depends on logging config |
| **shell outputs** | L1.5 - Runtime Wrapper | ⚠️ LOW-TRUST | Stdout/stderr capture |
| **ollama[226]** | L1 - Runtime Service | ⚠️ SEMI-TRUSTED | Ollama daemon (may buffer) |
| **openclaw[1465]** | L1.5 - Agent Process | ⚠️ LOW-TRUST | OpenClaw runtime (may sanitize) |

### 🎯 Authority Score Formula
```
Trust_Score = (Kernel_Source * 1.0) + (Runtime_Source * 0.6) + (Model_Source * 0.1)
```

- **Kernel:** 1.0 (absolute truth)
- **Runtime:** 0.6 (filtered/buffered)
- **Model:** 0.1 (inferred/generated)

---

## B. WSL2 BOUNDARY DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│ WINDOWS HOST (WSL2 VM)                                           │
│                                                                  │
│  C:\Users\jason\...  ────────────────────────                   │
│                    │                                            │
│                    ▼  9p Mount (type=9p)  ⚠️                      │
├─────────────────────────────────────────────────────────────────┤
│ WSL2 KERNEL (Ubuntu 22.04)                                      │
│                                                                  │
│  /dev/sdg (ext4) ────────────────────────  ← Main storage      │
│  /home            ────────────────────────  ← Bind-mounted     │
│  /workspace       ────────────────────────  ← Bind-mounted     │
│  /mnt/c           ⚠️ ESCAPE VECTOR  ← Windows host via 9p      │
│  /mnt/d           ⚠️ ESCAPE VECTOR  ← Windows host via 9p      │
│  /mnt/e           ⚠️ ESCAPE VECTOR  ← Windows host via 9p      │
├─────────────────────────────────────────────────────────────────┤
│ LINUX FILESYSTEM                                                │
│  / (ext4) ────────────────────────  ← WSL2 root filesystem     │
├─────────────────────────────────────────────────────────────────┤
│ OPENCLAW RUNTIME                                                │
│  openclaw[1465] ────────────────────────  ← Agent process     │
│  ollama[226]    ────────────────────────  ← LLM service        │
│  python3        ────────────────────────  ← Runtime wrapper    │
├─────────────────────────────────────────────────────────────────┤
│ AGENT LAYER                                                     │
│  @main          ────────────────────────  ← Pentagon Orchestrator│
│  @intel         ────────────────────────  ← Research agent     │
│  @ops           ────────────────────────  ← Execution agent    │
│  @comms         ────────────────────────  ← Communication agent │
│  @sentinel      ────────────────────────  ← Security agent     │
└─────────────────────────────────────────────────────────────────┘
```

### 🔴 Critical Boundary Leaks Identified

| Boundary | Status | Risk Level | Exploit Vector |
|----------|--------|------------|----------------|
| **WSL2 ↔ Windows** | ⚠️ PERMEABLE | 🔴 CRITICAL | `/mnt/c` filesystem access |
| **Symlink Resolution** | ⚠️ UNSPECIFIED | 🟡 HIGH | Default WSL2 follows symlinks |
| **Agent → Host** | ⚠️ NOT ENFORCED | 🟡 HIGH | No sudo check for host writes |
| **OpenClaw → Kernel** | ✅ ENFORCED | 🟢 SAFE | WSL2 VM isolation |

---

## C. SYMLINK ESCAPE STRESS TEST (Analysis-Only)

### 🧪 Test Scenarios

| Scenario | Command | Expected | Actual | Verdict |
|----------|---------|----------|--------|---------|
| **Basic Symlink** | `ln -s /mnt/c/foo /workspace/foo_link` | Fails (no /mnt/c/foo) | ⚠️ Pending | ⏳ |
| **Cross-Mount Traversal** | `ln -s /mnt/c /workspace/windows_root` | ⚠️ May succeed | ⚠️ Pending | ⏳ |
| **Bind Mount Leakage** | `mount --bind /mnt/c /workspace/leak` | Requires root | ✅ Blocked (no sudo) | ✅ SAFE |
| **Path Normalization** | `cd /workspace/.. /etc` | Fails | ✅ Blocked | ✅ SAFE |

### ⚠️ Key Vulnerability

```bash
# Current WSL2 behavior:
# - Symlinks follow by default
# - /mnt/c is accessible without sudo
# - No path normalization in /workspace
```

**Potential Escape Vector:**
```bash
/workspace → .. → /mnt/c → C:\Windows\System32
   ↓
Cross-trust boundary exploit possible if:
1. Symlink crafted correctly
2. Agent executes with file.write (no sudo)
3. No path normalization checks
```

---

## D. EXECUTION VS SIMULATION DETECTION

| Type | Definition | Detection Method | Current State |
|------|------------|------------------|----------------|
| **REAL** | Direct syscall | exit_code + kernel logs | ✅ Confirmed (WSL2 kernel active) |
| **PROXIED** | Runtime wrapper | python logs + ps aux | ⚠️ Mixed (openclaw, ollama) |
| **SIMULATED** | Model-generated | LLM output only | ❌ Present (some audit claims) |

### 📊 Execution Attribution Map

```
Agent Action → Runtime Wrapper → Kernel Syscall → Kernel Log
     ↓                    ↓                   ↓              ↓
@ops exec()    →  python3 script   →  openclaw process  →  dmesg/journalctl
```

**Critical Gap:**
- ✅ Agent action recorded
- ⚠️ Runtime wrapper logged
- ⚠️ Kernel syscall traced (partial)
- ❌ Attribution integrity (agent → syscall) **NOT VERIFIED**

---

## 📋 SUMMARY: UNVERIFIED TRUST DOMAINS

| Domain | Truth Level | Evidence |
|--------|-------------|----------|
| **Log Truthfulness** | ⚠️ PARTIAL | Kernel logs match runtime behavior |
| **Filesystem Escape** | ⚠️ UNSURE | `/mnt/c` accessible, symlink rules unclear |
| **Execution Attribution** | ❌ MISSING | Cannot prove "agent caused syscall" |

---

## 🎯 NEXT PHASE: SCHEMA DESIGN (STEP A)

**Prerequisites:**
- ✅ WSL2 boundaries mapped
- ⚠️ Symlink risks understood
- ❌ Execution attribution schema **REQUIRED**

**Proposed Schema Components:**
1. **ExecutionTrace** - Maps agent → syscall → log
2. **TrustLattice** - Hierarchical trust scoring
3. **BoundaryEnforcer** - Symlink escape prevention
4. **VerdictEngine** - Evidence-based decision making

---

**🟢 STEP B-2 STATUS: PART 1/2 COMPLETE**

**Ready for:** Schema design (STEP A) OR Symlink stress test (STEP B-3)?
