# ⚙️ Pentagon Workflow Protocol

**Owner:** @main (Orchestrator)
**Last updated:** 2026-05-22

## Execution Pipeline

```
User Request
     │
     ▼
┌─────────┐
│  @main   │── Analyze → Map agents → Dispatch
└────┬────┘
     │
     ├── 🔍 @intel  ──── Search (Memory → GitHub → Web)
     │                   Return findings + citations
     │
     ├── 🛠  @ops ────── Execute (Code → Docker → GitHub)
     │                   Return output + logs
     │
     ├── 🛡  @sentinel ── Verify (Security → Secret scan → Hallucination)
     │                   Return pass/fail + flags
     │
     └── 📢 @comms ───── Deliver (Format → Channel → Report)
                         Return delivery confirmation
     │
     ▼
┌─────────┐
│  @main   │── Synthesize → Final response
└─────────┘
```

## Agent Handoff Matrix

| From | To | Trigger | Protocol |
|------|----|---------|----------|
| @main | @intel | Need research/data | `sessions_send(agent="intel", message="...")` |
| @main | @ops | Need code/execution | `sessions_send(agent="ops", message="...")` |
| @ops | @sentinel | Before risky command | `sessions_send(agent="sentinel", message="scan:...")` |
| @intel | @sentinel | Before publishing findings | Cross-ref hallucination check |
| @sentinel | @comms | Alert triggered | High-priority notification |
| @comms | @main | Delivery complete | Report back with status |

## GitHub Integration Points

```
@intel ── gh search issues/code/repos → Context from OSS
@ops   ── gh repo/pr/issue/api       → Source control + automation
@sentinel── git_secret_scan()         → Pre-commit credential check
@comms ── gh repo view/issue list    → Status in reports
@main  ── gh auth status             → Bootstrap verification
```

## Service Dependency

```
OpenClaw Gateway
  ├── Qdrant (vector memory)  ← @intel reads/writes
  ├── Redis (cache/queue)     ← @ops manages
  ├── ComfyUI (image gen)     ← @ops starts/stops
  └── GitHub (source control) ← all agents reference
```

## Failure Recovery

| Failure | Action |
|---------|--------|
| @intel search fails | Fallback: Memory → GitHub → Web → @ops API |
| @ops command fails x2 | @main reads source code, retries |
| @sentinel times out | @main assumes Sentinel role |
| Git push rejected | `git pull --rebase` → retry |
| gh auth expired | Request user re-authenticate |
| Qdrant unreachable | `docker start qdrant` → retry |
