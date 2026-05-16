# Render Policy Routing Order

## Bug Report
**Issue:** OpenClaw replying "Stable. No user action required." to too many commands.
**Root cause:** Stable-state renderer is being applied globally before command intent routing.

## Required Fix: Command Routing Must Happen BEFORE Stable-State Rendering

### Routing Order (MANDATORY)

1. **Parse user command**
2. **Check explicit commands (do NOT suppress):**
   - show full telemetry
   - show full protocol
   - protocol show <name>
   - help
   - task-specific commands
   - troubleshooting commands
3. **If command is progress/status/quiet-soak-status AND system is stable:**
   - render exactly: "Stable. No user action required."
4. **For all other user commands:**
   - process normally
5. **Apply blocked-token stripping as final output step:**
   - NO_REPLY
   - INTERNAL_ONLY
   - CONTROL_ONLY
   - SYSTEM_ONLY

### Do NOT use stable response for:
- questions
- setup instructions
- troubleshooting requests
- protocol commands
- GitHub commands
- Discord commands
- RAG/search requests
- coding tasks
- user asks "what next?"
- user asks "how to..."
- user asks "show..."
- user asks "verify..."

### Only use stable response for:
- progress
- status
- h1 status
- quiet soak status
- observation status

## Regression Tests

1. **progress_stable_returns_one_line**
   - Expected: "Stable. No user action required."

2. **show_full_telemetry_not_suppressed**
   - Expected: Full telemetry report appears.

3. **protocol_show_render_policy_not_suppressed**
   - Expected: Protocol appears.

4. **normal_question_not_suppressed**
   - Input: "How do I verify GitHub CI?"
   - Expected: Actual helpful answer, not stable one-liner.

5. **troubleshooting_request_not_suppressed**
   - Input: "Something is wrong with Discord bot."
   - Expected: Troubleshooting response, not stable one-liner.

6. **blocked_tokens_still_stripped**
   - Expected: NO_REPLY and internal tokens never render.

## Expected Behavior After Patch

| Input | Expected Output |
|-------|-----------------|
| progress | "Stable. No user action required." |
| show full telemetry | Full metrics |
| protocol show render_policy | Protocol output |
| how do I verify GitHub CI? | Normal answer |
| Something is wrong with Discord bot. | Troubleshooting response |
