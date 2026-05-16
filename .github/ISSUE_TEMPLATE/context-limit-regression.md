# Fix context-limit regression from stable-status over-rendering

## 🐛 Symptom
Host chat still hits context limit reset:
"Context limit exceeded. I've reset our conversation to start fresh."

## 🎯 Expected Behavior
- `stable status` renders only: `"Stable. No user action required."`
- Normal questions and troubleshooting requests receive full answers
- Progress/status/h1 contexts get minimal one-liner
- Explicit `show full telemetry`/`show full protocol` commands allow full reports

## 🔍 Actual Behavior
- Stable status still renders telemetry/status blocks OR
- Stable response suppresses normal questions

## 🧵 Root Cause
- `stable-status` renderer bypasses command-aware render policy
- Over-rendering of: telemetry, H1 reports, setup reports, GitHub activity, timeline confirmations, protocol confirmations

## 💥 Impact
- Chat context pollution
- Frequent compaction/reset
- User frustration

## ✅ Fix
1. **Enforce command-aware minimal stable render globally**
2. **Add regression tests**
3. **Update CI verification**

## 📋 Fix Details

### render_policy.py routing order:
```
1. Parse user command
2. Check explicit commands:
   - show full telemetry
   - show full protocol
   - protocol show <name>
   - help
   - task-specific commands
   - troubleshooting commands
   - normal user questions
3. If command is progress/status/h1 status/quiet soak status AND system is stable:
   → render exactly: "Stable. No user action required."
4. For all other user commands:
   → process normally
5. Apply blocked-token stripping as final output step
```

### Stable-state minimal response applies ONLY when:
- Command is progress/status/h1 status/quiet soak status
- No warning
- No failure
- No degradation
- No invariant break
- No user decision required

### Suppress during stable status:
- GPU, VRAM, RPR, GAF, determinism, timeline
- GitHub activity, H1 phase reports, setup completion details
- Invariant confirmations, architecture confirmations, standing by messages

### Full reports allowed only for:
- `show full telemetry`
- `show full protocol`
- `protocol show <name>`

### Do NOT use stable response for:
- questions
- setup instructions
- troubleshooting requests
- protocol commands
- GitHub commands
- Discord commands
- RAG/search requests
- coding tasks
- "what next?"
- "how to..."
- "verify..."
- "show..."

## 🧪 Regression Tests

### test_render_policy.py tests:
- `progress_stable_returns_one_line`
- `status_stable_returns_one_line`
- `setup_stable_returns_one_line`
- `github_status_stable_returns_one_line`
- `h1_status_stable_returns_one_line`
- `no_internal_tokens_rendered`
- `show_full_telemetry_allows_full_report`
- `show_full_protocol_allows_full_report`
- `protocol_show_render_policy_allows_protocol`
- `normal_question_not_suppressed`
- `troubleshooting_request_not_suppressed`

### test_context_manager.py tests:
- `normal_prompt_allowed`
- `warning_threshold_triggers_warning`
- `oversized_prompt_blocked`
- `blocked_prompt_does_not_call_model`

### Synthetic strings:
```python
warning_text = "word " * 26000
block_text = "word " * 31000
```

## 📊 CI Checks (.github/workflows/openclaw-verify.yml)
- pytest tests/test_render_policy.py
- pytest tests/test_context_manager.py
- python scripts/runtime_verifier.py
- forbidden file check
- secret scan if available

## 🚫 Forbidden Files (must not enter Git)
- .env
- logs/
- traces/
- storage/
- qdrant/
- redis/
- models/
- *.jsonl
- Discord token
- GitHub token
- webhook URL
- browser profiles
- cookies

## 📝 Branch
`fix/context-limit-render-policy`

## 🔄 CI/CD
No automatic deployment. Wait for user approval before applying to live runtime.

## 📋 PR Checklist
- [ ] progress returns only stable one-liner
- [ ] status returns only stable one-liner
- [ ] setup status returns only stable one-liner
- [ ] normal questions are not suppressed
- [ ] troubleshooting requests are not suppressed
- [ ] no internal tokens rendered
- [ ] full telemetry still works when explicitly requested
- [ ] full protocol still works when explicitly requested
- [ ] context threshold tests pass
- [ ] runtime_verifier.py passes
- [ ] no live runtime modification during H1

---

*Labels: bug, context-manager, render-policy, h1-freeze, runtime, github*