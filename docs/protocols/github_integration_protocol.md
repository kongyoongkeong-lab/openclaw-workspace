# GitHub Integration Protocol

## Role Definition
**github_role:** external_learning_review_troubleshooting_channel

**runtime_control_surface:** false

**h1_compatibility:** conditional

## Workflow: Upgrade Path
1. Capture proposed upgrade
2. Create GitHub Issue
3. Create feature branch
4. Prepare patch offline
5. Add or update tests
6. Run runtime_verifier.py
7. Open Pull Request
8. Let GitHub Actions CI validate
9. Review results
10. Merge only if CI passes
11. Apply to live runtime only after H1 exits or user explicitly approves

## Workflow: Troubleshooting Path
1. Capture symptom
2. Check local logs, traces, snapshots, and runtime events
3. Search GitHub docs, source, issues, and PRs
4. Identify likely cause
5. Create or update GitHub Issue with:
   - symptom
   - expected behavior
   - actual behavior
   - trace_id if available
   - affected component
   - reproduction steps
   - suspected cause
6. Prepare fix in a branch
7. Add regression test
8. Run runtime_verifier.py
9. Run CI
10. Do not deploy unless H1 exits or user explicitly approves

## Issue Templates
Required issue labels:
- bug
- troubleshooting
- upgrade
- runtime
- discord
- github
- ci
- context-manager
- render-policy
- security
- rag
- qdrant
- redis
- h1-freeze

## Protocol Enforcement
**Blocked-Token Striper** applies as absolute final step before every chat response.

**Setup Completion Rule:**
If command is a setup completion and no user decision is required, render only:
"GitHub-assisted upgrade and troubleshooting workflow prepared. Runtime unchanged."
