# Fix: Context Limit Render Policy

## Issue Description
Stable response is incomplete for status/progress commands. The current behavior renders only "Stable. No user action" instead of the expected "Stable. No user action required."

## Root Cause
Render policy is applied too broadly, suppressing normal responses to status-only commands without checking for warnings, failures, or invariant breaks.

## Solution
Enforce command-aware render policy:
- **Status-only commands** (progress, status, h1 status, quiet soak status, session status) → render exactly "Stable. No user action required." when no warnings/failures present
- **Normal questions/troubleshooting** → do NOT apply stable response
- **Full telemetry/protocol show** → render full metrics/protocol
- **Blocked tokens** → strip before final output

## Files to Patch
1. `runtime/render/render_policy.py` - Core render routing logic
2. `tests/test_render_policy.py` - Regression tests for status-only behavior
3. `tests/test_context_manager.py` - Context overflow prevention
4. `.github/workflows/openclaw-verify.yml` - GitHub CI verification

## Local Draft Status
OFFLINE_PATCH_MODE: These files are local drafts for manual review and push.
