# Pentagon Team Communication Protocol

## 📡 Message Channels

### Primary Channel
- **Webchat (Direct)**: @main ↔ User
- All agent outputs route through @main for final delivery

### Inter-Agent Protocol (A2A)
```
@main → sessions_send(agent='agent_label', message='...')
@intel, @ops, @comms, @sentinel → isolated sessions
```

### Delivery Flow
1. **Request Analysis** (@main)
2. **Agent Dispatch** (to @intel/@ops/@comms/@sentinel)
3. **Sub-Agent Execution** (isolated sessions)
4. **Output Synthesis** (@main combines results)
5. **Final Delivery** (@main to user)

## 🎯 Message Format

### Sub-Agent Response
```markdown
**@agent_label**
```
- **Task:** <atomic operation>
- **Status:** <success|pending|failed>
- **Latency:** <elapsed time>
- **Artifacts:** <any generated files>
- **Next:** <dependencies or escalations>
```

### Synthesis Response
```markdown
**@main**
✅ **Task Complete**

**Summary:**
- Agents Deployed: @intel, @ops
- Latency: <total time>
- Artifacts: <links to files>

**Output:**
<formatted result>

🚀🤖
```

## 🚨 Escalation Path

### Failure Response (Level 1)
- **@ops** fails → Retry with `pty=true`
- **Retry fails** → Trigger `@sentinel` for diagnostics

### Critical Failure (Level 2)
- **@intel** unreachable → Switch to cached/context data
- **All agents** stall → **@main** resumes with full context

### VRAM Warning
- **Alert:** `@sentinel` if stack > 13.5GB
- **Action:** Route to smaller model or cloud fallback

## 🔒 Security Rules

- **@sentinel** vetts all `@ops` commands
- **Never leak:** Telegram tokens, API keys
- **Host isolation:** All writes in `/app/workspace/`
- **Sudo bypass:** Use Relational Memory flags for Docker

## 📊 Metrics

- **Delegation Latency:** Alert if >120s
- **VRAM Pressure:** Alert @sentinel if >13.5GB
- **Plan Drift:** If @ops and @intel conflict → re-align