# GitHub H1 Observation Mode Policy

**Status:** Active
**Mode:** External Learning / Review / Troubleshooting Channel
**Runtime Control:** False

## Allowed Activities
1. Read OpenClaw documentation
2. Review upstream source code
3. Search GitHub Issues/PRs
4. Document findings
5. Create/update GitHub Issues
6. Prepare patches offline
7. Create branches
8. Add/update tests
9. Run CI verification
10. Review CI results
11. Prepare post-H1 upgrade plans
12. Track troubleshooting history

## Blocked Activities
1. Live runtime modification ❌
2. Automatic deployment ❌
3. Webhook triggering runtime actions ❌
4. GitHub Actions controlling live runtime ❌
5. New agents ❌
6. New telemetry ❌
7. New governance abstractions ❌
8. New control layers ❌
9. Runtime self-correction ❌
10. Autonomous orchestration changes ❌
11. Automatic patch application ❌
12. ClawHub skill installation into production ❌

## Emergency Exception Protocol
If any of the following occurs:
- invariant break
- replay divergence
- snapshot corruption
- runtime crash loop
- token exposure
- secret leak
- data corruption
- security breach

Then:
1. Pause observation
2. Mark status as emergency
3. Create GitHub Issue
4. Prepare emergency patch branch
5. Run tests and verifier
6. Request user approval before deployment
7. Do not auto-deploy

## Protocol Enforcement
**Blocked-Token Striper** applies as absolute final step before every chat response.

**Blocked Tokens:**
- NO_REPLY
- INTERNAL_ONLY
- CONTROL_ONLY
- SYSTEM_ONLY

**Setup Completion Rule:**
If command is a setup completion and no user decision is required, render only:
"GitHub-assisted upgrade and troubleshooting workflow prepared. Runtime unchanged."
