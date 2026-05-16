# GitHub Usage Policy for H1 Observation Mode

## Current Mode
- github_role: external_learning_review_troubleshooting_channel
- runtime_control_surface: false
- h1_compatibility: conditional

## Runtime Control Surface
GitHub **must not** directly control or modify the live OpenClaw runtime during H1.
All modifications must be:
- Created in branches
- Tested offline
- Validated via CI
- Merged only after H1 exit or user approval

## Documentation & Knowledge Base
GitHub is the primary knowledge base for:
- Upstream changes
- Issue tracking
- Code review
- CI status
- Troubleshooting procedures

## Verification Workflow
All fixes must pass:
1. Python syntax check
2. YAML validity check
3. Forbidden file check
4. Secret scan
5. Runtime verifier
6. Render policy test
7. Context manager test
8. Discord router test (if changed)

## Merge Policy
- main = stable runtime only
- All upgrades/fixes = branch + PR
- Merge only after CI passes
- No merge during H1 without explicit user approval
