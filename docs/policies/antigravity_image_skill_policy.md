# Antigravity Image Skill Policy Guard

Mode: Documentation only. Runtime unchanged.

## Status

The Antigravity image generation skill is present on disk but inactive.

Under OpenClaw Stable v1.0 default mode, the Antigravity image generation skill is blocked by default and must remain inactive / quarantined / documentation-only.

## Default Allowed State

Default allowed state:

- inactive
- quarantined
- documentation-only

## Blocked by Default

The Antigravity image generation skill must not be activated without explicit user approval.

It must not read OAuth or browser auth profiles without explicit user approval.

It must not call external Google sandbox/API endpoints without explicit user approval.

It must not call external sandbox/API endpoints without approval.

It must not emit `MEDIA:` directly without explicit user approval.

It must not emit MEDIA directly without approval.

It must not be used through ClawHub without explicit user approval.

## Future Activation Requirements

Any future activation requires all of the following before use:

1. Explicit user approval.
2. Risk review.
3. Credential boundary check.
4. External endpoint review.
5. Runtime isolation plan.
6. Rollback plan.

## Validation Requirements

Before any approved activation, verify:

- the requested action is explicit and current;
- OAuth/browser profile access is bounded and reviewed;
- external Google sandbox/API endpoint use is reviewed;
- ClawHub activation/use is explicitly approved if involved;
- direct `MEDIA:` emission is explicitly approved if involved;
- no workflow files are changed unless separately approved;
- runtime isolation and rollback plans are documented.

## Stable v1.0 Guardrail

In Stable v1.0 default operation, this skill remains inactive. Documentation may reference it for audit and policy purposes only. No production activation, OAuth/browser auth profile read, external sandbox/API call, ClawHub activation, or direct media emission is permitted without explicit user approval.
