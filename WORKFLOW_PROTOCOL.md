# ⚙️ Pentagon Workflow Protocol v3.0

**Owner:** @main (Orchestrator)
**Last updated:** 2026-05-22 05:55 MYT
**Mode:** Cloud-Native (no local GPU/LLM)

---

## Execution Pipeline

```
User Request
     │
     ▼
┌─────────┐
│  @main   │── Analyze → Map agents → Dispatch
└────┬────┘
     │
     ├── 🔍 @intel  ───── Search (web_fetch → Tavily → Memory)
     │                    Return structured candidates + citations
     │
     ├── 🛠  @ops ─────── Execute (Shell → Python → Docker → GitHub)
     │                    Return output + logs + artifacts
     │
     ├── 🛡  @sentinel ── Verify (Security → Secret scan → Hallucination)
     │                    Return pass/fail + flags
     │
     └── 📢 @comms ────── Deliver (Format → Write → Channel → Report)
                          Return delivery confirmation
     │
     ▼
┌─────────┐
│  @main   │── Synthesize → UCG validation → Final response
└─────────┘
```

---

## Agent Models

| Agent  | Primary | Fallback | Timeout |
|--------|---------|----------|---------|
| @main  | deepseek/deepseek-v4-flash | gemini-2.5-flash-lite | 600s |
| @intel | deepseek/deepseek-v4-flash | gemini-2.5-flash-lite | 120s |
| @ops   | deepseek/deepseek-v4-flash | gemini-2.5-flash-lite | 300s |
| @comms | deepseek/deepseek-v4-flash | gemini-2.5-flash-lite | 60s |
| @sentinel | deepseek/deepseek-v4-flash | gemini-2.5-flash-lite | 30s |

---

## Agent Handoff Matrix

| From | To | Trigger | Protocol |
|------|----|---------|----------|
| @main | @intel | Need research/data | `sessions_send(agent="intel", message="...")` |
| @main | @ops | Need code/execution | `sessions_send(agent="ops", message="...")` |
| @ops | @sentinel | Before risky command | `sessions_send(agent="sentinel", message="scan:...")` |
| @intel | @sentinel | Before publishing findings | Cross-ref hallucination check |
| @sentinel | @comms | Alert triggered | High-priority notification |
| @comms | @main | Delivery complete | Report back with status |
| @main | @comms | Need output formatting | Pass raw content + target channel |

---

## Skills Registry

| Agent | Active Skills |
|-------|--------------|
| @main | agent-team-orchestration, skill-vetter |
| @intel | tavily, pdf, python-executor |
| @ops | terminal-command-execution, python-executor, file-organizer-skill, image-ocr |
| @comms | file-organizer-skill |
| @sentinel | skill-vetter, python-executor |

---

## GitHub Integration Points

```
@intel  ── gh search issues/code/repos → Context from OSS
@ops   ── gh repo/pr/issue/api       → Source control + automation
@sentinel── git_secret_scan()         → Pre-commit credential check
@comms ── gh repo view/issue list    → Status in reports
@main  ── gh auth status             → Bootstrap verification
```

**Known Repos:**
- kongyoongkeong-lab/openclaw-workspace (agent configs + memory)
- kongyoongkeong-lab/openclaw-config (gateway config)

---

## Service Dependency

```
OpenClaw Gateway (cloud-native)
  ├── API Providers: DeepSeek, Google, OpenAI
  ├── Search: Tavily, Google Web Search
  ├── Qdrant (vector memory)     ← @intel reads/writes
  ├── Redis (cache/queue)        ← @ops manages
  └── GitHub (source control)    ← all agents reference
```

---

## Workflow Routines

### Daily News (今日新闻)

1. Cache check → `news/YYYY-MM-DD-daily-news.md`
2. @intel: Fetch Telegram sources + web search (max 2 Tavily)
3. @main: UCG validation + priority filter
4. @main: Format report (tea-shop Chinese, mobile-friendly)
5. Archive to `news/` + deliver

### Daily AI (今日AI)

1. @intel: Multi-search across model/chip/agent/regulation/Malaysia angles
2. @main: Deduplicate + validate (7-day freshness)
3. @main: Format with 30s exec summary + categories
4. Archive to `news/ai/` + deliver

---

## Failure Recovery

| Failure | Action |
|---------|--------|
| @intel search fails | Fallback: Memory → GitHub → Web → @ops API |
| @ops command fails x2 | @main reads source code, retries |
| @sentinel times out (>5s) | @main assumes Sentinel role |
| Git push rejected | `git pull --rebase` → retry |
| gh auth expired | Request user re-authenticate |
| Qdrant unreachable | `docker start qdrant` → retry |
| Tavily quota exhausted | Fallback to web_fetch + free search |

---

## System Constraints

- **Cloud-native only** — no local GPU/LLM inference
- **Privacy** — Never leak Telegram Bot Token, Tavily API keys, GitHub PAT
- **Sandbox** — All writes stay within `/home/jason2ykk/.openclaw/workspace/`
- **Compaction model** — deepseek/deepseek-v4-flash (not ollama)
- **Search budget** — 2 Tavily/run (standard), unlimited in deep mode
