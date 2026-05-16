# NO_REPLY & Internal Token Stripping Filter

## Context
H1 Observation Mode Active • Strict Output Filtering

---

## 🎯 Problem

During final output rendering, the following tokens appear in chat:

- `NO_REPLY`
- `INTERNAL_ONLY`
- `CONTROL_ONLY`
- `SYSTEM_ONLY`

These tokens indicate internal state/control but **must not** appear in user-facing messages.

---

## ✅ Solution: Global Output Filter

### Filter Logic

```yaml
apply_to:
  - final_responses
  - protocol_reports
  - setup_reports
  - telemetry_reports
  - progress_reports
  - status_reports
  - github_reports

strip_tokens:
  - NO_REPLY
  - INTERNAL_ONLY
  - CONTROL_ONLY
  - SYSTEM_ONLY

apply_before: chat_send

preserve:
  - user_content
  - tool_results
  - structured_data
```

### Implementation

**Step 1:** Intercept final response generation

**Step 2:** Scan for forbidden tokens

**Step 3:** Remove tokens and metadata markers

**Step 4:** Send clean output to chat

---

## 📝 Examples

### Before (Dirty)

```text
GitHub H1 policy installed. No runtime impact.
NO_REPLY
```

### After (Clean)

```text
GitHub H1 policy installed. No runtime impact.
```

---

## 🛡️ Enforcement

This filter is now:

- ✅ **Global** - Applied to all response types
- ✅ **Pre-send** - Runs before chat delivery
- ✅ **Hard** - Blocks forbidden tokens regardless of context

---

## 📊 Compliance

```yaml
compliance:
  h1_mode: true
  filter_active: true
  tokens_stripped: 4
  enforcement: global
```

---

*Last updated: 2026-05-15 17:21+08:00*  
*Filter Version: 1.0 (H1 Strict)*
